"""Small official CFTC TFF futures-only weekly positioning sample."""
import argparse
import pandas as pd
import requests
from .engine import Data
from .events_data import save
from .acquire import stamp

def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);a=p.parse_args();d=Data(a.as_of);dest=d.base/'cot.json.gz'
    if dest.exists():return
    codes=['13874A','209742','043602','042601']
    cols=['report_date_as_yyyy_mm_dd','contract_market_name','cftc_contract_market_code','open_interest_all','lev_money_positions_long','lev_money_positions_short','asset_mgr_positions_long','asset_mgr_positions_short','dealer_positions_long_all','dealer_positions_short_all']
    start=str((pd.Timestamp(a.as_of)-pd.DateOffset(years=2)).date());end=str((pd.Timestamp(a.as_of)-pd.Timedelta(days=3)).date())
    params={'$select':','.join(cols),'$where':"cftc_contract_market_code in ('"+"','".join(codes)+f"') AND report_date_as_yyyy_mm_dd >= '{start}' AND report_date_as_yyyy_mm_dd <= '{end}'",'$order':'report_date_as_yyyy_mm_dd','$limit':1000}
    url='https://publicreporting.cftc.gov/resource/gpe5-46if.json';r=requests.get(url,params=params,timeout=25);r.raise_for_status();rows=r.json()
    if not rows or len(rows)>=1000:raise ValueError('Unexpected CFTC coverage')
    save(dest,dict(source=url,retrieved_at=stamp(),report_type='TFF futures only',rows=rows));print('CFTC',len(rows),'weekly records',flush=True)
if __name__=='__main__':main()
