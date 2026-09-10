"""Bounded public Sentinel-2 COG window acquisition; no full-tile downloads.

Location review is a separate, frozen registry. Unreviewed locations are never
queried. Scientific raw bands remain local; only derived RGB/NDVI maps publish.
"""
import argparse
import gzip
import hashlib
import io
import json
import math
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import numpy as np
import requests

from .store import ROOT, DATA, read_json, write_json

API = 'https://earth-search.aws.element84.com/v1'
COLLECTION = 'sentinel-2-c1-l2a'
HOST = 'e84-earth-search-sentinel-data.s3.us-west-2.amazonaws.com'
BANDS = ('red', 'green', 'blue', 'nir', 'scl')
MAX_CANDIDATES = 36
MODEL_SPEC = 1
SIDE_M = 4000
PIXELS = 400
MIN_CLEAR = .70
MIN_CORE_CLEAR = .85
MAX_TRANSFER = 192 * 1024 * 1024


def stamp():
    return datetime.now(timezone.utc).isoformat()


def pack(path, value):
    content = gzip.compress(json.dumps(value, ensure_ascii=False, allow_nan=False).encode(), mtime=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp'); tmp.write_bytes(content); tmp.replace(path)


def unpack(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def registry():
    data = read_json(ROOT/'config/satellite_sites.json')
    ids = set()
    for s in data['sites']:
        if not re.fullmatch(r'ST_[A-Z_]+', s['id']) or s['id'] in ids:
            raise ValueError('Invalid or duplicate site ID')
        ids.add(s['id'])
        if s['location_status'] == 'reviewed':
            if not (-85 < s['lat'] < 85 and -180 < s['lon'] < 180):
                raise ValueError('Invalid facility coordinates')
            if not s.get('coordinate_source') or not s.get('sources') or not s.get('scope'):
                raise ValueError('Reviewed location needs evidence and observation scope')
    if len(ids) != 22:
        raise ValueError('Preserve all 22 original facility slots')
    return data


class Transfer:
    """All remote raster reads pass through strict HTTP Range validation."""
    def __init__(self, limit=MAX_TRANSFER, session=None):
        self.limit = limit; self.used = 0; self.requests = 0
        self.session = session or requests.Session()

    def get(self, url, start, size):
        u = urlparse(url)
        if u.scheme != 'https' or u.netloc != HOST or not u.path.startswith('/sentinel-2-c1-l2a/') or u.query:
            raise ValueError('Only public, unsigned Earth Search C1 raster assets are accepted')
        if size < 1 or size > 4*1024*1024 or self.used + size > self.limit:
            raise ValueError('Satellite transfer budget exceeded')
        self.requests += 1
        with self.session.get(url, headers={'Range': f'bytes={start}-{start+size-1}',
                'Accept-Encoding': 'identity'}, stream=True, timeout=30, allow_redirects=False) as r:
            # Never read a server's full-image response, including HTTP 200.
            if r.status_code != 206:
                raise ValueError('Raster server did not honor bounded HTTP Range')
            match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', r.headers.get('Content-Range', ''))
            if not match:
                raise ValueError('Missing raster byte-range contract')
            lo, hi, total = map(int, match.groups())
            if lo != start or hi != min(start+size, total)-1 or not 0 < total < 2**32:
                raise ValueError('Incorrect raster byte range')
            content = r.raw.read(hi-lo+2)
            self.used += len(content)
            if len(content) != hi-lo+1:
                raise ValueError('Truncated or oversized raster range')
            return content, total


class RangeFile(io.RawIOBase):
    """Rasterio's opener uses seek/read, without its eager MemoryFile path."""
    def __init__(self, url, transfer):
        super().__init__(); self.url = url; self.transfer = transfer; self.pos = 0
        first, self.size = transfer.get(url, 0, 16384)
        self.cache = {(0, len(first)): first}

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos

    def seek(self, offset, whence=0):
        p = offset if whence == 0 else self.pos+offset if whence == 1 else self.size+offset if whence == 2 else -1
        if p < 0: raise ValueError('Invalid raster seek')
        self.pos = p; return p

    def read(self, size=-1):
        if size < 0: raise ValueError('Whole raster reads are prohibited')
        size = min(size, max(0, self.size-self.pos))
        if not size: return b''
        start = self.pos; end = start+size
        for (lo, hi), content in self.cache.items():
            if lo <= start and end <= hi:
                self.pos = end; return content[start-lo:end-lo]
        content, total = self.transfer.get(self.url, start, size)
        if total != self.size: raise ValueError('Raster changed during acquisition')
        self.cache[(start, end)] = content; self.pos = end
        return content


def open_band(asset, transfer):
    import rasterio
    url = asset['href']
    def opener(path, mode='rb'):
        if path != url or mode not in ('r', 'rb'):
            raise FileNotFoundError(path)
        return RangeFile(url, transfer)
    return rasterio.open(url, opener=opener, driver='GTiff')


def quality(scl):
    clear = np.isin(scl, [4,5,6]); h,w = scl.shape
    return dict(coverage=float(np.mean(scl!=0)),clear_fraction=float(clear.mean()),
        core_clear_fraction=float(clear[h//2-50:h//2+50,w//2-50:w//2+50].mean()),
        point_clear_fraction=float(clear[h//2-5:h//2+5,w//2-5:w//2+5].mean()))


def usable(q):
    return q.get('coverage',0)>=.98 and q.get('clear_fraction',0)>=MIN_CLEAR and q.get('core_clear_fraction',0)>=MIN_CORE_CLEAR and q.get('point_clear_fraction',0)>=.95


def scene_window(scene, site, transfer):
    """Read quality first, then four native 10 m bands on one aligned UTM grid."""
    import rasterio
    from rasterio.warp import transform
    from rasterio.windows import Window, from_bounds, bounds as window_bounds
    from rasterio.enums import Resampling
    assets = scene['assets']
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', GDAL_PAM_ENABLED='NO'):
        with open_band(assets['red'], transfer) as src:
            x, y = transform('EPSG:4326', src.crs, [site['lon']], [site['lat']])
            row, col = src.index(x[0], y[0]); w = Window(col-PIXELS//2, row-PIXELS//2, PIXELS, PIXELS)
            if w.col_off < 0 or w.row_off < 0 or w.col_off+w.width > src.width or w.row_off+w.height > src.height:
                raise ValueError('Observation window crosses this tile boundary')
            if not np.isclose(src.transform.a, 10) or not np.isclose(src.transform.e, -10):
                raise ValueError('Expected 10 m Sentinel grid')
            crs = src.crs; transform_ = src.window_transform(w); bounds = window_bounds(w, src.transform)
        with open_band(assets['scl'], transfer) as src:
            if src.crs != crs: raise ValueError('SCL CRS differs from reflectance')
            sw = from_bounds(*bounds, transform=src.transform)
            scl = src.read(1, window=sw, out_shape=(PIXELS, PIXELS), resampling=Resampling.nearest)
        meta = dict(crs=str(crs), transform=list(transform_)[:6], **quality(scl),
                    width=PIXELS, height=PIXELS, native_resolution_m=10, classification_resolution_m=20)
        if not usable(meta):
            return None, meta
        arrays = {'scl': scl}
        for band in BANDS[:-1]:
            with open_band(assets[band], transfer) as src:
                if src.crs != crs or src.window_transform(w) != transform_:
                    raise ValueError('Reflectance bands do not share the native grid')
                arrays[band] = src.read(1, window=w)
    return arrays, meta


def reflectance(raw, asset):
    b = asset['raster:bands'][0]
    scale, offset = float(b['scale']), float(b['offset'])
    if not math.isfinite(scale) or not math.isfinite(offset) or scale <= 0:
        raise ValueError('Invalid surface reflectance calibration')
    out = raw.astype(np.float32)*scale+offset
    out[raw == b['nodata']] = np.nan
    return out


def derived(arrays, assets):
    channels = {k: reflectance(arrays[k], assets[k]) for k in BANDS[:-1]}
    clear = np.isin(arrays['scl'], [4, 5, 6])
    red, nir = channels['red'], channels['nir']; denominator = nir+red
    valid = clear & np.isfinite(red) & np.isfinite(nir) & (red >= 0) & (nir >= 0) & (denominator > 1e-6)
    ndvi = np.full(red.shape, np.nan, np.float32)
    np.divide(nir-red, denominator, out=ndvi, where=valid)
    rgb = np.stack([channels[k] for k in ('red', 'green', 'blue')])
    rgb[:, ~clear] = np.nan
    return rgb, ndvi, dict(valid_fraction=float(valid.mean()),
        ndvi_median=float(np.nanmedian(ndvi)) if valid.any() else None,
        vegetation_fraction=float(np.mean(ndvi[valid] >= .3)) if valid.any() else None)


def search(site, base, now):
    key = base/'satellite_search'/(site['id']+'-'+site_signature(site)[:16]+'-c'+str(MAX_CANDIDATES)+'.json.gz')
    if key.exists(): return unpack(key)
    # A bbox search followed by actual raster boundary checking avoids city-centre images.
    dy = .03; dx = dy/math.cos(math.radians(site['lat']))
    params = dict(collections=COLLECTION, bbox=','.join(map(str,[site['lon']-dx, site['lat']-dy, site['lon']+dx, site['lat']+dy])),
        datetime=(now-timedelta(days=60)).isoformat()+'/'+now.isoformat(), limit=MAX_CANDIDATES, sortby='-properties.datetime')
    with requests.get(API+'/search', params=params, stream=True, timeout=40) as r:
        r.raise_for_status(); content = r.raw.read(2*1024*1024+1, decode_content=True)
    if len(content) > 2*1024*1024: raise ValueError('STAC search exceeds2MiB')
    result = json.loads(content); items = result.get('features')
    if not isinstance(items, list) or len(items) > MAX_CANDIDATES:
        raise ValueError('Unexpected STAC search result')
    result['checked_at'] = stamp(); result['request'] = params; pack(key, result)
    return result


def collect(d, now=None, only=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None: raise ValueError('Observation cutoff needs a timezone')
    destination = d.base/'satellite_collection.json.gz'
    prior_path = d.resource('satellite_collection.json.gz')
    prior = unpack(prior_path) if prior_path.exists() else {'sites': []}
    old = {s['id']: s for s in prior['sites']}
    transport = Transfer(); rows = []; sites = registry()
    for site in sites['sites']:
        row = dict(id=site['id'], status='pending_location', checked_at=stamp(), scene=None, attempts=[])
        if site['location_status'] != 'reviewed': rows.append(row); continue
        if only and site['id'] not in only:
            rows.append(old.get(site['id'], dict(row, status='not_collected'))); continue
        try:
            response = search(site, d.base, now)
            candidates = sorted(response['features'], key=lambda s:s['properties']['datetime'], reverse=True)
            row['status'] = 'no_clear_scene'
            for scene in candidates:
                if scene['collection'] != COLLECTION or not re.fullmatch(r'S2[ABC]_T[A-Z0-9]+_\d{8}T\d{6}_L2A', scene['id']):
                    raise ValueError('Unexpected Sentinel scene identity')
                captured = datetime.fromisoformat(scene['properties']['datetime'].replace('Z','+00:00'))
                if not now-timedelta(days=60) <= captured <= now: raise ValueError('Scene outside observation window')
                previous = old.get(site['id'], {}).get('scene')
                if previous and previous['id'] == scene['id'] and previous.get('site_signature') == site_signature(site) and usable(previous):
                    row.update(status='ok', scene=previous); break
                try:
                    arrays, m = scene_window(scene, site, transport)
                except ValueError as exc:
                    if str(exc) == 'Observation window crosses this tile boundary':
                        row['attempts'].append(dict(id=scene['id'], reason='tile_boundary')); continue
                    raise
                row['attempts'].append(dict(id=scene['id'], **{k:m[k] for k in ['clear_fraction','coverage','core_clear_fraction','point_clear_fraction']}))
                if arrays is None: continue
                _, _, metrics = derived(arrays, scene['assets'])
                if metrics['valid_fraction'] < MIN_CLEAR: continue
                path = 'satellite/'+site['id']+'/'+scene['id']+'.npz'
                buf = io.BytesIO(); np.savez_compressed(buf, **arrays); content = buf.getvalue()
                target = d.base/path; target.parent.mkdir(parents=True, exist_ok=True)
                tmp = target.with_suffix('.tmp'); tmp.write_bytes(content); tmp.replace(target)
                info = dict(id=scene['id'], captured_at=scene['properties']['datetime'], retrieved_at=stamp(),
                    source=API+'/collections/'+COLLECTION+'/items/'+scene['id'], collection=COLLECTION,
                    assets={k:scene['assets'][k] for k in BANDS}, raw_file=path, sha256=hashlib.sha256(content).hexdigest(),
                    site_signature=site_signature(site), tile_cloud_percent=scene['properties'].get('eo:cloud_cover'),
                    **m, **metrics)
                row.update(status='ok', scene=info); break
            if row['status'] != 'ok' and old.get(site['id'], {}).get('scene'):
                row.update(status='stale', scene=old[site['id']]['scene'])
        except (ValueError, RuntimeError, requests.RequestException, OSError) as exc:
            previous = old.get(site['id'], {}).get('scene')
            row.update(status='stale' if previous else 'error', scene=previous, error_type=type(exc).__name__, error=str(exc)[:200])
        rows.append(row)
        print('SATELLITE', site['id'], row['status'], row['scene']['captured_at'] if row['scene'] else '', flush=True)
    result = dict(model_spec=MODEL_SPEC, retrieved_at=stamp(), observation_cutoff=now.isoformat(), sites=rows,
        range_requests=transport.requests, raster_bytes=transport.used, registry_reviewed_at=sites['reviewed_at'])
    pack(destination, result); return result


def site_signature(site):
    return hashlib.sha256(json.dumps({k:site[k] for k in ['id','lat','lon','scope']}, sort_keys=True).encode()).hexdigest()


def main():
    from .engine import Data
    p = argparse.ArgumentParser(); p.add_argument('--as-of', required=True); p.add_argument('--only', nargs='*'); a = p.parse_args()
    d = Data(a.as_of); result = collect(d, only=a.only)
    print('Satellite windows', sum(s['scene'] is not None for s in result['sites']), 'of', len(result['sites']))


if __name__ == '__main__': main()
