"""Small annual UN Comtrade TOTAL-export snapshots, bounded and cached on the PC."""
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import requests
from .engine import Data
from .events_data import read, save
from .store import ROOT, read_json
from .acquire import stamp

API = 'https://comtradeapi.un.org/public/v1/preview/C/A/HS'
REFS = {'reporters': 'https://comtradeapi.un.org/files/v1/app/reference/Reporters.json',
        'partners': 'https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json'}
FOLDER = 'trade/'
CONFIG = read_json(ROOT/'config/trade_areas.json')
AREAS = [dict(zip(CONFIG['columns'], row)) for row in CONFIG['areas']]


def query(code, year):
    return dict(period=str(year), reporterCode=str(code), cmdCode='TOTAL', flowCode='X',
                partner2Code='0', customsCode='C00', motCode='0', maxRecords=500,
                includeDesc='true', breakdownMode='classic')


def normalized(packet, code, year):
    """Reject truncation and mixed scope; no mirror imports or missing-to-zero."""
    data = packet.get('data')
    if packet.get('error') or not isinstance(data, list):
        raise ValueError('Comtrade error or schema change')
    if packet.get('count') != len(data) or len(data) >= 500:
        raise ValueError('Incomplete or capped Comtrade response')
    rows = {}
    for r in data:
        if any(r.get(k) != v for k, v in {
            'typeCode': 'C', 'freqCode': 'A', 'reporterCode': code,
            'period': str(year), 'refYear': year, 'flowCode': 'X',
            'cmdCode': 'TOTAL', 'partner2Code': 0, 'customsCode': 'C00', 'motCode': 0,
            'classificationSearchCode': 'HS', 'aggrLevel': 0}.items()):
            raise ValueError('Comtrade scope mismatch')
        partner = r.get('partnerCode')
        if not isinstance(partner, int) or isinstance(partner, bool) or partner < 0:
            raise ValueError('Invalid partner')
        value = r.get('primaryValue')
        try:
            if isinstance(value, bool) or value is None: raise ValueError()
            amount = Decimal(str(value))
            if not amount.is_finite() or amount < 0: raise ValueError()
        except (InvalidOperation, ValueError):
            raise ValueError('Invalid current USD export value') from None
        row = dict(partner=partner, usd=format(amount, 'f'),
                   reported=r.get('isReported'), aggregate=r.get('isAggregate'),
                   classification=r.get('classificationCode'))
        if not isinstance(row['reported'], bool) or not isinstance(row['aggregate'], bool):
            raise ValueError('Missing source reporting flags')
        if partner in rows and rows[partner] != row:
            raise ValueError('Conflicting bilateral observations')
        rows[partner] = row
    if rows and (0 not in rows or Decimal(rows[0]['usd']) <= 0):
        raise ValueError('Missing positive world-export denominator')
    if rows and any(Decimal(r['usd']) > Decimal(rows[0]['usd']) * Decimal('1.000001') for r in rows.values()):
        raise ValueError('Bilateral export exceeds world denominator')
    return sorted(rows.values(), key=lambda r: r['partner'])


def verify_references(packets):
    result = {}
    for kind, prefix in [('reporters', 'reporter'), ('partners', 'Partner')]:
        rows = {r['id']: r for r in packets[kind]['results']}
        for a in AREAS:
            row = rows.get(a['code'])
            if not row or row.get(prefix+'Code') != a['code']:
                raise ValueError('Country/area code absent from official reference')
            if a['id'] != 'S19' and row.get(prefix+'CodeIsoAlpha2') != a['id']:
                raise ValueError('Country ISO does not match Comtrade code')
            if a['id'] == 'S19' and row.get(prefix+'CodeIsoAlpha3') != 'S19':
                raise ValueError('Statistical area 490 identity changed')
            if kind == 'reporters':
                result[a['code']] = dict(official_name=row[prefix+'Desc'],
                                         coverage=row.get('reporterNote', ''), is_group=row['isGroup'])
    return result


def download(session, url, params=None):
    with session.get(url, params=params, timeout=(10, 35), stream=True) as response:
        response.raise_for_status()
        body = bytearray()
        for chunk in response.iter_content(16384):
            body.extend(chunk)
        packet = json.loads(body, parse_float=Decimal)
        return packet, len(body), hashlib.sha256(body).hexdigest()


def recent(packet, days, now):
    try:
        t = datetime.fromisoformat(packet['checked_at'])
        return t.tzinfo is not None and 0 <= (now-t).total_seconds() < days*86400
    except (ValueError, KeyError, TypeError): return False


def collect(d, session=None, pause=time.sleep):
    session = session or requests.Session()
    year = int(d.as_of[:4]) - CONFIG['year_lag']
    now = datetime.now(timezone.utc)
    manifest = dict(checked_at=stamp(), year=year, source=API, requests=0, received_bytes=0, areas=[])
    last_file = d.resource(FOLDER+'collection.json.gz')
    last = read(last_file) if last_file.exists() else {}
    last_checks = {r['code']: r for r in last.get('areas', [])} if last.get('year') == year else {}
    cached = d.resource(FOLDER+'references.json.gz')
    refs = read(cached) if cached.exists() else {}
    if not recent(refs, 180, now):
        try:
            packets = {}
            for kind, url in REFS.items():
                manifest['requests'] += 1
                packets[kind], size, _ = download(session, url)
                manifest['received_bytes'] += size; pause(2)
            verify_references(packets)
            refs = dict(checked_at=stamp(), packets=packets)
            save(d.base/FOLDER/'references.json.gz', refs)
        except Exception as e:
            manifest['reference_error'] = type(e).__name__
            if not refs:
                save(d.base/FOLDER/'collection.json.gz', manifest)
                return manifest
    identities = verify_references(refs['packets'])
    stopped = False
    for i, a in enumerate(AREAS):
        name = FOLDER+f'{year}/{a["code"]}.json.gz'
        path = d.resource(name); previous = read(path) if path.exists() else {}
        if last_checks.get(a['code'], {}).get('checked_at'):
            previous = dict(previous, checked_at=last_checks[a['code']]['checked_at'])
        rows = previous.get('rows', [])
        state = 'reused'
        if not recent(previous, CONFIG['refresh_days'], now):
            if stopped:
                state = 'deferred'
            else:
                try:
                    manifest['requests'] += 1
                    raw, size, sha = download(session, API, query(a['code'], year))
                    manifest['received_bytes'] += size
                    rows = normalized(raw, a['code'], year)
                    # Empty API result is a successful query, not an observed zero.
                    if not rows and previous.get('rows'):
                        raise ValueError('Previously observed annual data disappeared')
                    packet = dict(year=year, reporter=a['code'], rows=rows,
                                  checked_at=stamp(), retrieved_at=stamp(), source=API,
                                  query=query(a['code'], year), sha256=sha,
                                  **identities[a['code']])
                    if rows == previous.get('rows'):
                        packet['retrieved_at'] = previous['retrieved_at']
                    else:
                        save(d.base/name, packet)
                    previous = packet
                    state = 'ok' if rows else 'unavailable'
                except Exception as e:
                    state = 'error'
                    rows = previous.get('rows', [])
                    if isinstance(e, requests.HTTPError) and e.response is not None and e.response.status_code in (401, 403, 429):
                        stopped = True
                    # Record exception type only; never expose transport/session details.
                    manifest.setdefault('errors', []).append(dict(code=a['code'], error=type(e).__name__))
                finally: pause(2)
        manifest['areas'].append(dict(code=a['code'], state=state, observations=len(rows),
                                      retrieved_at=previous.get('retrieved_at'), checked_at=previous.get('checked_at')))
        print('TRADE', i+1, len(AREAS), a['id'], year, state, len(rows), flush=True)
    save(d.base/FOLDER/'collection.json.gz', manifest)
    return manifest


def main():
    p = argparse.ArgumentParser(); p.add_argument('--as-of', required=True)
    a = p.parse_args(); collect(Data(a.as_of))


if __name__ == '__main__': main()
