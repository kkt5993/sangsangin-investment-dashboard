"""Local-only, dated price vintages. No raw prices under GitHub Pages."""
from pathlib import Path
import hashlib
import json
import os
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get('SANGSANGIN_DATA_DIR', ROOT.parent/'sangsangin-investment-data'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(obj, ensure_ascii=False, allow_nan=False, separators=(',', ':'))+'\n', encoding='utf-8')
    temp.replace(path)


def load_prices(vintage, as_of):
    base = DATA / vintage
    manifest = read_json(base/'manifest.json')
    prices = {}
    for symbol, item in manifest['instruments'].items():
        if item.get('status') != 'ok':
            continue
        path = base / item['file']
        if path.parent.resolve() != base.resolve() or digest(path) != item['sha256']:
            raise ValueError('Cache integrity failure: '+symbol)
        d = pd.read_csv(path, index_col='date', parse_dates=['date'])
        # Reference-date comparison identifies mixed conventions in the source.
        # KR ETF adjusted close; US ETFs raw close (no dividend reinvestment).
        field = 'adjusted_close' if symbol.endswith('.KS') else 'close'
        prices[symbol] = d[field].loc[:as_of]
    return prices, manifest
