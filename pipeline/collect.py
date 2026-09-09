"""Explicit, serial Yahoo daily-price acquisition with dated caches.

Run: python -m pipeline.collect --as-of 2026-09-08
Re-running a vintage skips successful files. No schedules, retry loops or site calls.
"""
import argparse
from datetime import date, datetime, timedelta, timezone
import importlib.metadata
import time
import pandas as pd
import yfinance as yf
from .store import DATA, digest, read_json, write_json
from .universe import symbols


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--as-of', default=str(date.today()-timedelta(days=1)))
    p.add_argument('--start', default='2015-01-01')
    p.add_argument('--symbols', nargs='+', help='Optional subset of configured symbols')
    args = p.parse_args()
    as_of = date.fromisoformat(args.as_of)
    if as_of >= date.today():
        p.error('Use a completed date before today; intraday bars are not accepted.')
    if date.fromisoformat(args.start) >= as_of:
        p.error('start must precede as-of')
    selected = args.symbols or symbols()
    if set(selected)-set(symbols()):
        p.error('Symbols must be declared in pipeline/universe.py')
    base = DATA / args.as_of
    base.mkdir(parents=True, exist_ok=True)
    mf = base/'manifest.json'
    manifest = read_json(mf) if mf.exists() else dict(
        provider='Yahoo Finance via yfinance', vintage=args.as_of, requested_as_of=args.as_of,
        requested_start=args.start, price_field='Adj Close',
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        yfinance_version=importlib.metadata.version('yfinance'), instruments={})
    if manifest['requested_start'] != args.start:
        p.error('Existing vintage uses another start date; do not mix contracts.')
    errors = []
    for i, symbol in enumerate(selected):
        old = manifest['instruments'].get(symbol, {})
        if old.get('status') == 'ok' and (base/old['file']).exists() and digest(base/old['file']) == old['sha256']:
            print(f'[{i+1}/{len(selected)}] {symbol} cache', flush=True)
            continue
        footprint = sum(f.stat().st_size for f in DATA.rglob('*') if f.is_file())
        if footprint >= 32*1024*1024:
            raise SystemExit('32 MiB cache limit reached. Ask user before growing the data store.')
        if i:
            time.sleep(2)
        item = dict(retrieved_at=datetime.now(timezone.utc).isoformat())
        try:
            t = yf.Ticker(symbol)
            frame = t.history(start=args.start, end=str(as_of+timedelta(days=1)),
                              auto_adjust=False, actions=True, repair=False, timeout=20)
            if frame.empty or 'Adj Close' not in frame:
                raise ValueError('No adjusted daily observations returned')
            d = pd.DataFrame({
                'date': frame.index.tz_localize(None).strftime('%Y-%m-%d'),
                'close': frame['Close'].to_numpy(),
                'adjusted_close': frame['Adj Close'].to_numpy(),
                'dividend': frame['Dividends'].to_numpy(),
                'split': frame['Stock Splits'].to_numpy(),
            }).dropna(subset=['adjusted_close'])
            if (d.adjusted_close <= 0).any() or d.date.duplicated().any() or not d.date.is_monotonic_increasing:
                raise ValueError('Invalid price index or non-positive price')
            d = d[d.date <= args.as_of]
            if d.empty:
                raise ValueError('No observations at or before as-of')
            path = base/(symbol.replace('^', 'INDEX_')+'.csv.gz')
            d.to_csv(path, index=False, compression=dict(method='gzip', mtime=0), float_format='%.10g')
            if footprint + path.stat().st_size > 32*1024*1024:
                raise SystemExit('32 MiB cache budget exceeded by final response; ask before collecting more.')
            meta = t.get_history_metadata()  # already cached by history; no quote/info fanout
            item.update(status='ok', file=path.name, sha256=digest(path), rows=len(d),
                        first_date=d.date.iloc[0], last_date=d.date.iloc[-1],
                        currency=meta.get('currency'), exchange_timezone=meta.get('exchangeTimezoneName'),
                        short_name=meta.get('shortName') or meta.get('longName'), bytes=path.stat().st_size)
            print(f'[{i+1}/{len(selected)}] {symbol} {len(d)} rows {item["last_date"]}', flush=True)
        except Exception as e:
            # Deliberately avoid response bodies, cookies and exception payloads in manifests.
            item.update(status='error', error_type=type(e).__name__)
            errors.append(symbol)
            print(f'[{i+1}/{len(selected)}] {symbol} failed ({type(e).__name__})', flush=True)
        manifest['instruments'][symbol] = item
        write_json(mf, manifest)
    print('Collection complete. Errors: '+(', '.join(errors) or 'none'), flush=True)
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
