import io
import gzip
import json
import tempfile
from pathlib import Path
from datetime import datetime,timezone
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from pipeline import satellite_data as sat


URL = 'https://'+sat.HOST+'/sentinel-2-c1-l2a/fixture/B04.tif'


class Response:
    def __init__(self, data, lo, hi, status=206):
        self.status_code = status
        self.headers = {'Content-Range':f'bytes {lo}-{hi}/{len(data)}'}
        self.raw = io.BytesIO(data[lo:hi+1]); self.entered = False
    def __enter__(self): self.entered = True; return self
    def __exit__(self, *args): return False


class Session:
    def __init__(self, data, status=206): self.data = data; self.status = status; self.calls = []
    def get(self, url, **kwargs):
        self.calls.append(kwargs)
        lo, hi = map(int, kwargs['headers']['Range'][6:].split('-'))
        self.last = Response(self.data, lo, min(hi,len(self.data)-1),self.status)
        return self.last


class SatelliteTests(unittest.TestCase):
    def test_desert_rgb_exposure_does_not_change_ndvi_or_statistics(self):
        from pipeline.satellite_views import images
        a={k:np.full((4,4),4000,dtype=np.uint16) for k in sat.BANDS[:-1]}
        a['nir'][:]=5000;a['scl']=np.full((4,4),5,np.uint8)
        assets={k:{'raster:bands':[dict(scale=.0001,offset=-.1,nodata=0)]} for k in sat.BANDS[:-1]}
        scene=dict(assets=assets,crs='EPSG:32639',transform=[10,0,330000,0,-10,2800000],width=4,height=4)
        standard,bounds,stats=images(a,scene)
        desert,new_bounds,new_stats=images(a,scene,.65)
        self.assertNotEqual(standard['rgb'],desert['rgb'])
        self.assertEqual(standard['ndvi'],desert['ndvi'])
        self.assertEqual((bounds,stats),(new_bounds,new_stats))
        with self.assertRaises(ValueError):images(a,scene,0)

    def test_search_cache_changes_with_observation_location_and_candidate_limit(self):
        site=dict(id='ST_TEST',lat=35,lon=125,scope='fixture')
        response=SimpleNamespace(raise_for_status=lambda:None,
            raw=SimpleNamespace(read=lambda *a,**kw:b'{"features":[]}'))
        with tempfile.TemporaryDirectory() as folder, patch.object(sat.requests,'get') as get:
            get.return_value.__enter__.return_value=response
            now=datetime(2026,9,10,tzinfo=timezone.utc);base=Path(folder)
            sat.search(site,base,now);sat.search(site,base,now)
            self.assertEqual(get.call_count,1)
            sat.search(dict(site,lon=126),base,now)
            self.assertEqual(get.call_count,2)
            with patch.object(sat,'MAX_CANDIDATES',12):sat.search(site,base,now)
            self.assertEqual(get.call_count,3)
            self.assertEqual(len(list((base/'satellite_search').glob('*.json.gz'))),3)

    def test_cloud_over_factory_rejected_despite_clear_surroundings(self):
        scl=np.full((400,400),5,dtype=np.uint8)
        self.assertTrue(sat.usable(sat.quality(scl)))
        scl[150:250,150:250]=8;q=sat.quality(scl)
        self.assertGreater(q['clear_fraction'],.9);self.assertFalse(sat.usable(q))
        scl[:]=5;scl[195:205,195:205]=3;q=sat.quality(scl)
        self.assertGreater(q['core_clear_fraction'],.95);self.assertFalse(sat.usable(q))

    def test_calibration_before_ndvi_and_quality_mask(self):
        # DN 3000/2000 with -0.1 offset: reflectance .2/.1, NDVI1/3, not DN1/5.
        a = {k:np.full((2,3),2000,dtype=np.uint16) for k in sat.BANDS[:-1]}
        a['nir'][:] = 3000; a['scl'] = np.array([[4,5,6],[8,3,0]],np.uint8)
        assets = {k:{'raster:bands':[dict(scale=.0001,offset=-.1,nodata=0)]} for k in sat.BANDS[:-1]}
        rgb, ndvi, stats = sat.derived(a, assets)
        np.testing.assert_allclose(ndvi[0],1/3,rtol=1e-6)
        self.assertTrue(np.isnan(ndvi[1]).all()); self.assertTrue(np.isnan(rgb[:,1]).all())
        self.assertEqual(stats['valid_fraction'],.5)
        a['red'][0,0] = 0; a['nir'][0,1] = 500; a['red'][0,2] = 1000; a['nir'][0,2] = 1000
        self.assertTrue(np.isnan(sat.derived(a,assets)[1]).all())

    def test_missing_calibration_rejected(self):
        with self.assertRaises(KeyError): sat.reflectance(np.ones((2,2)),{'raster:bands':[dict(scale=.0001,nodata=0)]})

    def test_range_seek_cache_and_whole_file_rejection(self):
        data=bytes(range(256))*300; session=Session(data); transfer=sat.Transfer(session=session)
        f=sat.RangeFile(URL,transfer)
        self.assertEqual(f.read(10),data[:10]); self.assertEqual(len(session.calls),1)
        f.seek(20000); self.assertEqual(f.read(99),data[20000:20099]); f.seek(-10,2)
        self.assertEqual(f.read(100),data[-10:]); self.assertEqual(f.read(100),b'')
        with self.assertRaises(ValueError): f.read()
        self.assertEqual(transfer.used,16384+99+10)

    def test_unbounded_or_wrong_host_response_never_read(self):
        session=Session(b'a'*100000,status=200); transfer=sat.Transfer(session=session)
        with self.assertRaises(ValueError): transfer.get(URL,0,100)
        self.assertEqual(session.last.raw.tell(),0)
        for url in ['http://'+sat.HOST+'/x',URL+'?token=x','https://other.example/x']:
            with self.assertRaises(ValueError): transfer.get(url,0,100)
        self.assertEqual(len(session.calls),1)

    def test_transfer_limit_and_incorrect_range(self):
        session=Session(b'a'*100000); transfer=sat.Transfer(limit=100,session=session)
        with self.assertRaises(ValueError): transfer.get(URL,0,101)
        self.assertEqual(len(session.calls),0)
        with patch.object(session,'get',return_value=Response(b'a'*100,5,20)):
            with self.assertRaises(ValueError): transfer.get(URL,0,16)

    def test_actual_gdal_opener_reads_only_needed_ranges(self):
        import rasterio
        from rasterio.io import MemoryFile
        from rasterio.transform import from_origin
        data=np.arange(512*512,dtype=np.uint16).reshape(512,512)
        with MemoryFile() as memory:
            with memory.open(driver='GTiff',width=512,height=512,count=1,dtype='uint16',
                    crs='EPSG:32611',transform=from_origin(500000,4900000,10,10),tiled=True,
                    blockxsize=128,blockysize=128,compress='deflate') as ds: ds.write(data,1)
            content=memory.read()
        session=Session(content); transfer=sat.Transfer(session=session)
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',GDAL_PAM_ENABLED='NO'):
            with sat.open_band({'href':URL},transfer) as ds:
                result=ds.read(1,window=((220,230),(260,270)))
        np.testing.assert_array_equal(result,data[220:230,260:270])
        self.assertLess(transfer.used,len(content))

    def test_all_reference_facility_slots_preserved(self):
        data=sat.registry(); self.assertEqual(len(data['sites']),22)
        self.assertEqual(len({s['id'] for s in data['sites']}),22)
        for s in data['sites']:
            if s['location_status']=='pending': self.assertIsNone(s['lat']); self.assertIsNone(s['lon'])

    def test_failure_retains_original_scene_dates_and_pending_never_queries(self):
        site=dict(id='ST_TEST',location_status='reviewed',lat=35,lon=125,scope='fixture')
        previous=dict(id='older',captured_at='2026-08-01T00:00:00Z',retrieved_at='2026-08-02T00:00:00Z',sha256='unchanged')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);parent=root/'prior.json.gz';parent.write_bytes(gzip.compress(json.dumps({'sites':[dict(id='ST_TEST',scene=previous)]}).encode()))
            base=root/'next';base.mkdir();d=SimpleNamespace(base=base,resource=lambda key:parent)
            with patch.object(sat,'registry',return_value={'reviewed_at':'2026-09-10','sites':[site,dict(id='ST_PENDING',location_status='pending')]}),patch.object(sat,'search',side_effect=ValueError('provider unavailable')) as query:
                result=sat.collect(d,now=datetime(2026,9,10,tzinfo=timezone.utc))
            self.assertEqual(query.call_count,1)
            self.assertEqual(result['sites'][0]['status'],'stale');self.assertEqual(result['sites'][0]['scene'],previous)
            self.assertEqual(result['sites'][1]['status'],'pending_location');self.assertIsNone(result['sites'][1]['scene'])

    def test_recurring_publication_copies_new_images_alongside_json(self):
        from pipeline.refresh import copy_satellite_outputs
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'stage/docs/data/satellite';target=root/'public/docs/data/satellite'
            source.mkdir(parents=True);target.mkdir(parents=True)
            (source/'ST_TEST-rgb.png').write_bytes(b'new validated image');(target/'ST_TEST-rgb.png').write_bytes(b'old image')
            copy_satellite_outputs(root/'stage',root/'public')
            self.assertEqual((target/'ST_TEST-rgb.png').read_bytes(),b'new validated image')
            self.assertFalse(list(target.glob('*.tmp')))
            (source/'unreviewed.png').write_bytes(b'bad')
            with self.assertRaises(ValueError):copy_satellite_outputs(root/'stage',root/'public')
            self.assertFalse((target/'unreviewed.png').exists())


if __name__=='__main__': unittest.main()
