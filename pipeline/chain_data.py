"""Small company profile snapshots for the explicit global research universe."""
import argparse
import contextlib
import io
import logging
import math
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit
import yfinance as yf
from .acquire import stamp
from .engine import Data
from .events_data import read, save
from .store import ROOT, read_json

FOLDER = 'chain/'
PROFILE = FOLDER + 'profiles.json.gz'
TTL_HOURS = 24
FIELDS = ['longName', 'shortName', 'city', 'state', 'country', 'website', 'marketCap',
          'currency', 'sector', 'industry', 'regularMarketTime']


def settings():
    c = read_json(ROOT / 'config/chain_universe.json')
    symbols = [r['symbol'] for r in c['companies']]
    if len(symbols) != len(set(symbols)) or len(symbols) > 200:
        raise ValueError('Company identity/scope')
    ids = [s['id'] for s in c['sectors']]
    if len(ids) != len(set(ids)):
        raise ValueError('Repeated research sector')
    for sector in c['sectors']:
        if any(s not in symbols for s in sector['symbols']):
            raise ValueError('Unknown sector member')
        if len(sector['symbols']) != len(set(sector['symbols'])):
            raise ValueError('Repeated sector member')
    return c


def normalize(symbol, info, now):
    if info.get('symbol') != symbol or info.get('quoteType') != 'EQUITY':
        raise ValueError('Profile symbol/type mismatch')
    if not info.get('longName') or not info.get('country'):
        raise ValueError('Incomplete company identity')
    row = {k: info.get(k) for k in FIELDS}
    for key in FIELDS:
        if key not in ['marketCap', 'regularMarketTime'] and row[key] is not None:
            if not isinstance(row[key], str) or len(row[key]) > 500:
                raise ValueError('Profile field size/type')
    cap = row['marketCap']
    if cap is not None and (isinstance(cap, bool) or not isinstance(cap, (int, float))
                            or not math.isfinite(cap) or not 0 < cap < 1e17):
        raise ValueError('Market capitalization range')
    quoted = row['regularMarketTime']
    if quoted is not None:
        if isinstance(quoted, bool) or not isinstance(quoted, (int, float)) or not math.isfinite(quoted):
            raise ValueError('Invalid quote timestamp')
        if quoted < 946684800 or quoted > now.timestamp() + 300:
            raise ValueError('Quote timestamp range')
    if row['website']:
        url = urlsplit(row['website'])
        if url.scheme not in ['http', 'https'] or not url.hostname or url.username or url.password:
            row['website'] = None
    return row


def age_hours(value, now):
    try:
        t = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if t.tzinfo is None:
            return float('inf')
        age = (now - t).total_seconds() / 3600
        return age if age >= 0 else float('inf')
    except (ValueError, TypeError, AttributeError):
        return float('inf')


def collect(d, fetch=None, pause=time.sleep, now=None, config=None):
    now = now or datetime.now(timezone.utc)
    config = config or settings()
    path = d.resource(PROFILE)
    old = read(path) if path.exists() else {}
    records = dict(old.get('companies', {}))
    prior_path = d.resource(FOLDER + 'collection.json.gz')
    prior = read(prior_path) if prior_path.exists() else {}
    previous = {r['symbol']: r for r in prior.get('companies', [])}
    report = dict(checked_at=now.isoformat(),companies=[])
    fetch = fetch or (lambda symbol: yf.Ticker(symbol).get_info())
    failures = 0
    halted = False
    changed = False
    logging.getLogger('yfinance').setLevel(logging.CRITICAL)
    for company in config['companies']:
        symbol = company['symbol']
        record = records.get(symbol, {})
        recent_error = previous.get(symbol, {})
        requested = False
        error = None
        state = 'reused'
        if age_hours(record.get('checked_at'), now) >= TTL_HOURS:
            if halted:
                state = 'deferred'
            elif recent_error.get('state') in ['error','error-backoff'] and age_hours(recent_error.get('attempted_at'), now) < 1:
                state = 'error-backoff'
            else:
                requested = True
                pause(1)
                try:
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        info = fetch(symbol)
                    data = normalize(symbol, info, now)
                    retrieved = record.get('retrieved_at') if data == record.get('data') else stamp()
                    records[symbol] = dict(symbol=symbol,data=data,retrieved_at=retrieved,
                                           checked_at=stamp(),source='Yahoo Finance company profile')
                    record = records[symbol]
                    state = 'ok'
                    changed = True
                    failures = 0
                except Exception as exc:
                    error = type(exc).__name__
                    state = 'error'
                    failures += 1
                    if 'RateLimit' in error or failures >= 3:
                        halted = True
        report['companies'].append(dict(symbol=symbol,state=state,requested=requested,error_type=error,
            attempted_at=now.isoformat() if requested else recent_error.get('attempted_at'),
            retrieved_at=record.get('retrieved_at'),checked_at=record.get('checked_at')))
        if requested:
            print('CHAIN',symbol,state,flush=True)
        # Small metadata checkpoint; never clone price histories or analyst reports.
        if changed and len(report['companies']) % 20 == 0:
            save(d.base / PROFILE,dict(schema=1,companies=records));changed = False
    if changed:
        save(d.base / PROFILE,dict(schema=1,companies=records))
    save(d.base / (FOLDER + 'collection.json.gz'),report)
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--as-of',required=True)
    args = p.parse_args()
    d=Data(args.as_of)
    report = collect(d)
    print('CHAIN requested',sum(r['requested'] for r in report['companies']),flush=True)
    from .chain_geo import collect as collect_locations
    collect_locations(d)
    from .chain_evidence import collect as collect_evidence
    evidence = collect_evidence(d)
    print('CHAIN source checks',sum(r['requested'] for r in evidence['attempts']),flush=True)


if __name__ == '__main__':
    main()
