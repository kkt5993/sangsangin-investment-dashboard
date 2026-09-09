"""Offline audit against an explicitly supplied, local reference JSON.

python scripts/compare_reference.py --reference ../aragorn_investium_study/source/data/rs.json --vintage 2026-09-08
Does not copy reference rows/images or make any network requests.
"""
import argparse
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.store import load_prices, read_json
from pipeline.build import make_snapshots


def compare(reference, vintage):
    as_of=reference['as_of'][:10]
    prices,manifest=load_prices(vintage,as_of)
    rs,_=make_snapshots(prices,manifest,as_of)
    reference_rows={r['name']:r for r in reference['table'] if r['group'] in ['KR','US']}
    differences=[]
    for p in rs['pairs']:
        if p['z'] is None:
            continue
        r=reference_rows[p['name']]
        spread=float(re.search(r'[+-]?\d+(?:\.\d+)?',r['value']).group())
        differences.append(dict(id=p['id'],market=p['market'],spread_abs_error_pp=abs(p['spread_pp']-spread),z_abs_error=abs(p['z']-r['z'])))
    summary=dict(reference_as_of=reference['as_of'], vintage=vintage, compared=len(differences),
                 unavailable=[p['id'] for p in rs['pairs'] if p['z'] is None],
                 note='One historical snapshot is a diagnostic, not proof of engine equivalence.', markets={})
    for market in ['KR','US']:
        d=[r for r in differences if r['market']==market]
        if d:
            summary['markets'][market]=dict(n=len(d),spread_rounding_matches=sum(r['spread_abs_error_pp']<.051 for r in d),
                max_spread_abs_error_pp=round(max(r['spread_abs_error_pp'] for r in d),4),
                mean_z_abs_error=round(sum(r['z_abs_error'] for r in d)/len(d),4),
                max_z_abs_error=round(max(r['z_abs_error'] for r in d),4))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--vintage',required=True)
    args=p.parse_args()
    print(json.dumps(compare(read_json(args.reference),args.vintage),ensure_ascii=False,indent=2))
