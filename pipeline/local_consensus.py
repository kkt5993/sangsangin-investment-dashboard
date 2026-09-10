"""Narrow read-only import of local consensus; never copies the source database."""
from .store import data_base
import argparse,gzip,json
import pandas as pd
from .store import DATA,write_json
from .engine import clean_json
from .acquire import stamp
def main():
    p=argparse.ArgumentParser();p.add_argument('database');p.add_argument('--as-of',default='2026-09-08');a=p.parse_args()
    import duckdb
    c=duckdb.connect(a.database,read_only=True)
    f=c.execute("SELECT as_of,market,ticker,name,item_code,item_name,unit,period,value FROM qw_snapshot WHERE as_of<=? AND item_code IN ('E121500.M','E122710.M','E121000.M','E211000.M') AND period IN ('2024AS','2025AS','2026AS','2027AS','2028AS')",[a.as_of]).df();c.close()
    f['as_of']=f.as_of.astype(str)
    if f.empty:raise ValueError('No supported local consensus rows')
    # Preserve the source observation date, source unit and fiscal year on every row.
    f=f.sort_values('as_of').drop_duplicates(['ticker','item_code','period'],keep='last')
    result=dict(source='QuantiWise existing local snapshot',imported_at=stamp(),as_of=str(f.as_of.max()),rows=f.to_dict('records'))
    encoded=json.dumps(clean_json(result),ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8');compressed=gzip.compress(encoded,mtime=0)
    (data_base(a.as_of)/'local_consensus.json.gz').write_bytes(compressed);print('Imported local consensus',len(f),'rows; snapshot',result['as_of'])
if __name__=='__main__':main()
