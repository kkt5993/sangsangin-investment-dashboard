"""Reviewed company geography. Document checks do not revalidate claim semantics."""
import copy
import gzip
import hashlib
import math
import re
import time
from datetime import date, datetime, timezone
from urllib.parse import urlsplit
import requests
from .store import ROOT, read_json
from .events_data import read, save
from .acquire import stamp
from .chain_data import age_hours

MANIFEST = 'chain/evidence_sources.json.gz'


def settings():
    c = read_json(ROOT / 'config/chain_evidence.json')
    from .chain_data import settings as universe
    validate(c, {r['symbol'] for r in universe()['companies']})
    return c


def validate(c, symbols):
    if c['version'] != 1 or len(c['sources']) > 200:raise ValueError('Evidence version/scope')
    def sources(row):
        if not row['source_ids'] or any(s not in c['sources'] for s in row['source_ids']):
            raise ValueError('Missing evidence source')
    for id, s in c['sources'].items():
        url = urlsplit(s['url'])
        if not re.fullmatch('[a-z0-9_]+', id) or url.scheme != 'https' or not url.hostname or url.username or url.password:
            raise ValueError('Source identity/URL')
        reviewed = datetime.fromisoformat(s['reviewed_at'])
        if reviewed.tzinfo is None:raise ValueError('Review timezone')
        if s.get('published_on') and date.fromisoformat(s['published_on']) > reviewed.date():raise ValueError('Source date')
    for id, p in c['places'].items():
        if id != p['id'] or not id.isdigit() or not re.fullmatch('[A-Z]{2}', p['country']):raise ValueError('Place identity')
        for key, limit in [('lat', 90), ('lon', 180)]:
            v = p[key]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or abs(v) > limit:
                raise ValueError('Coordinate range')
        if p['source'] != 'https://www.geonames.org/' + id + '/':raise ValueError('Coordinate provenance')
    addresses = set()
    from .chain_geo import COUNTRIES
    for a in c['addresses']:
        if a['symbol'] not in symbols or a['symbol'] in addresses or a['place_id'] not in c['places']:raise ValueError('Address identity')
        if COUNTRIES.get(a['profile_match']['country']) != c['places'][a['place_id']]['country']:raise ValueError('Address country')
        addresses.add(a['symbol']);sources(a)
    ids = set()
    for r in c['routes']:
        if r['id'] in ids or r['owner'] not in symbols or r['kind'] not in ['valuechain', 'export', 'logistics']:raise ValueError('Route identity/kind')
        ids.add(r['id']);sources(r)
        if not all(re.fullmatch('[A-Z]{2}', r[k]) for k in ['from_country', 'to_country']):raise ValueError('Route country')
        if not isinstance(r['directed'], bool):raise ValueError('Route direction')
        reviewed = datetime.fromisoformat(r['reviewed_at'])
        if reviewed.tzinfo is None or (r.get('observed_on') and date.fromisoformat(r['observed_on']) > reviewed.date()):raise ValueError('Route date')
        if r.get('quantity'):
            q = r['quantity'];v = q['value']
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 or not q['unit']:raise ValueError('Route quantity/unit')
    for b in c['business']:
        if b['symbol'] not in symbols:raise ValueError('Business identity')
        sources(b)


def enrich(companies, config=None):
    c = config or settings();result = copy.deepcopy(companies)
    addresses = {r['symbol']:r for r in c['addresses']};business = {r['symbol']:r for r in c['business']}
    for row in result:
        a = addresses.get(row['symbol'])
        if a:
            row['official_address'] = a
            matches = all(row.get(k) == v for k, v in a['profile_match'].items())
            row['address_profile_match'] = matches
            # A later provider move must not silently retain a stale override.
            if matches:
                row['location'] = dict(c['places'][a['place_id']], profile_city=row['city'],
                    profile_country=row['country'], match_method='reviewed_official_address')
        if row['symbol'] in business:row['business_evidence'] = business[row['symbol']]
    return result


def fetch(url):
    with requests.get(url, stream=True, timeout=(10, 35), headers={'User-Agent':'SangsanginResearch/1.0'}) as response:
        if response.status_code != 200:raise ValueError('HTTP ' + str(response.status_code))
        data = bytearray()
        for part in response.iter_content(65536):
            data.extend(part)
        if not data:raise ValueError('Empty source')
    return bytes(data)


def collect(d, fetcher=fetch, pause=time.sleep, now=None, config=None, manifest=MANIFEST, folder="chain/evidence"):
    c = config or settings();now = now or datetime.now(timezone.utc);path = d.resource(manifest)
    records = copy.deepcopy(read(path).get('sources', {})) if path.exists() else {}
    attempts = [];failed_hosts = set()
    for id, source in c['sources'].items():
        old = records.get(id, {})
        if old.get('url') != source['url']:old = {};records.pop(id, None)
        if age_hours(old.get('attempted_at'), now) < 30 * 24:
            attempts.append(dict(id=id,state='cached',requested=False));continue
        host = urlsplit(source['url']).hostname
        if host in failed_hosts:
            attempts.append(dict(id=id,state='deferred',requested=False));continue
        row = dict(old, url=source['url'], attempted_at=now.isoformat())
        try:
            blob = fetcher(source['url'])
            if not blob:raise ValueError('Empty source')
            sha = hashlib.sha256(blob).hexdigest();changed = bool(old.get('sha256') and old['sha256'] != sha)
            if old.get('sha256') != sha:
                packed = gzip.compress(blob);target = d.base / (folder + '/' + id + '.html.gz')
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_suffix('.tmp');temporary.write_bytes(packed);temporary.replace(target)
                row['retrieved_at'] = now.isoformat()
            row.update(sha256=sha, bytes=len(blob), checked_at=now.isoformat(), error_type=None,
                       changed_since_review=bool(old.get('changed_since_review')) or changed)
            state = 'changed' if row['changed_since_review'] else 'available'
        except Exception as exc:
            row['error_type'] = type(exc).__name__;state = 'error';failed_hosts.add(host)
        records[id] = row;attempts.append(dict(id=id, state=state, requested=True));pause(2)
    result = dict(sources=records, attempts=attempts, checked_at=stamp());save(d.base / manifest, result)
    return result
