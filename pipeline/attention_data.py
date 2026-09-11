"""Wikimedia daily user pageviews, revised overlap and cache; no model calls."""
import argparse, copy, time
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote
import requests
from .guru_data import read, save, resources
from .store import ROOT, read_json

FILE = 'attention/pageviews.json.gz'
API = 'https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/'


def settings():
    return read_json(ROOT / 'config/attention_pages.json')


def age(value, now):
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            return float('inf')
        return (now - dt).total_seconds() / 3600
    except (AttributeError, TypeError, ValueError):
        return float('inf')


def url(project, title, start, end):
    return API + project + '/all-access/user/' + quote(title.replace(' ', '_'), safe='') + '/daily/' + start.replace('-', '') + '00/' + end.replace('-', '') + '00'


def normalize(raw, project, title, start, end):
    items = raw.get('items')
    if not isinstance(items, list) or not items:
        raise ValueError('Missing daily observations')
    rows = {}
    for r in items:
        if (r.get('project') != project.removesuffix('.org') or r.get('article', '').replace('_', ' ') != title.replace('_', ' ')
                or r.get('access') != 'all-access' or r.get('agent') != 'user' or r.get('granularity') != 'daily'):
            raise ValueError('Pageview identity or population mismatch')
        ts = r.get('timestamp', '')
        if len(ts) != 10 or not ts.isdigit() or not ts.endswith('00'):
            raise ValueError('Daily UTC timestamp required')
        dt = date(int(ts[:4]), int(ts[4:6]), int(ts[6:8])).isoformat()
        v = r.get('views')
        if not start <= dt <= end or dt in rows or type(v) is not int or v < 0:
            raise ValueError('Invalid day, duplicate or count')
        rows[dt] = v
    # Missing days are gaps, never zero-fill. The complete-window calculator checks them.
    return [dict(date=k, views=rows[k]) for k in sorted(rows)]


def collect(d, session=None, now=None, pause=time.sleep):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Timezone required')
    cfg = settings(); path = d.resource(FILE)
    old = read(path) if path.exists() else {'pages': {}}
    report = dict(attempted_at=now.isoformat(), status='reused', requests=0, errors=[])
    last = old.get('collection', {})
    if last.get('status') in ['error', 'access_refused'] and 0 <= age(last.get('attempted_at'), now) < 1:
        return dict(report, status='backoff')
    end = min(date.fromisoformat(d.as_of), now.astimezone(timezone.utc).date() - timedelta(days=2)).isoformat()
    packet = copy.deepcopy(old); packet['project'] = cfg['project']
    own = session is None; session = session or requests.Session()
    try:
        for spec in cfg['pages']:
            prior = packet['pages'].get(spec['symbol'], {})
            same = all(prior.get(k) == spec[k] for k in ['title', 'pageid', 'wikidata']) and prior.get('project') == cfg['project']
            if same and prior.get('requested_end') == end and not prior.get('error') and 0 <= age(prior.get('checked_at'), now) < 24:
                continue
            prior = prior if same else {}
            old_points = prior.get('points', [])
            start = max(date.fromisoformat(old_points[-1]['date']) - timedelta(days=6), date.fromisoformat(end) - timedelta(days=59)).isoformat() if old_points else (date.fromisoformat(end) - timedelta(days=59)).isoformat()
            if start > end:
                continue  # Historical rebuild does not overwrite a later cache.
            target = url(cfg['project'], spec['title'], start, end); report['requests'] += 1; report['status'] = 'ok'; pause(1)
            try:
                response = session.get(target, timeout=(10, 30), headers={'User-Agent': 'SangsanginResearch/1.0 (+https://github.com/kkt5993/sangsangin-investment-dashboard)'})
                response.raise_for_status()
                points = normalize(response.json(), cfg['project'], spec['title'], start, end)
                merged = {r['date']: r for r in old_points if r['date'] < start or r['date'] > end}
                merged.update({r['date']: r for r in points})
                packet['pages'][spec['symbol']] = dict(**spec, project=cfg['project'], points=[merged[k] for k in sorted(merged)],
                    checked_at=now.isoformat(), retrieved_at=now.isoformat(), requested_end=end, source_url=target, error=None)
            except Exception as exc:
                code = getattr(getattr(exc, 'response', None), 'status_code', None)
                report['errors'].append(dict(symbol=spec['symbol'], type=type(exc).__name__, http_status=code))
                packet['pages'][spec['symbol']] = dict(prior, checked_at=now.isoformat(), error=type(exc).__name__)
                report['status'] = 'access_refused' if code in [401, 403, 429] else 'error'
                if code in [401, 403, 429]:
                    break
        if report['errors'] and report['status'] == 'ok':
            report['status'] = 'error'
        if report['requests']:
            packet['collection'] = report; save(d.base / FILE, packet)
    finally:
        if own:
            session.close()
    return report


def main():
    p = argparse.ArgumentParser(); p.add_argument('--as-of', required=True); args = p.parse_args()
    import json
    print(json.dumps(collect(resources(args.as_of))))


if __name__ == '__main__':
    main()
