"""Small, dated flow inputs; KRX auth only behind an explicit CLI flag."""
import argparse,contextlib,io,json,logging,time
import pandas as pd
import requests,yfinance as yf
from .store import data_base
from .engine import Data,number
from .events_data import save,read
from .acquire import stamp,get_bytes
from .flow_catalog import US_STOCKS,ETF_DEFINITIONS
from .options_data import normalize,parse_contracts,FLOW_SCOPE

def upcoming(d,now):
    from .subview_modules import event_data
    from .financial_modules import frame
    out=[]
    for symbol,raw in event_data(d).items():
        for date,row in frame(raw.get('earnings_dates')).iterrows():
            t=pd.Timestamp(date)
            if t.tzinfo and now<t<=now+pd.Timedelta(days=21) and number(row.get('Reported EPS')) is None:out.append((symbol,t.isoformat()))
    return sorted(out,key=lambda a:a[1])[:8]

def collect_us(d,allow_cboe_download=False):
    folder=d.base/'flows';folder.mkdir(exist_ok=True);logging.getLogger('yfinance').setLevel(logging.CRITICAL)
    fields=['longName','currency','quoteType','totalAssets','marketCap','floatShares','sharesShort','shortPercentOfFloat','shortRatio','dateShortInterest','sharesShortPreviousMonthDate','regularMarketTime','regularMarketPrice']
    symbols=sorted(set(US_STOCKS)|{a['symbol'] for a in ETF_DEFINITIONS})
    for symbol in symbols:
        dest=folder/('info_'+symbol+'.json.gz')
        if dest.exists():continue
        try:
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):info=yf.Ticker(symbol).get_info()
            out=dict(symbol=symbol,source='Yahoo Finance quote summary',retrieved_at=stamp(),status='ok',info={k:info.get(k) for k in fields})
            if out['info']['currency']!='USD':raise ValueError('Missing or unexpected USD currency')
        except Exception as e:out=dict(symbol=symbol,retrieved_at=stamp(),status='error',error_type=type(e).__name__,info={})
        save(dest,out);print('FLOW INFO',symbol,out['status'],flush=True);time.sleep(.4)
    now=pd.Timestamp.now(tz='UTC');events=dict(upcoming(d,now));save(folder/'earnings_targets.json.gz',dict(retrieved_at=now.isoformat(),events=events))
    collect_us_options(d,events,allow_download=allow_cboe_download)
    good_info=sum(read(folder/('info_'+s+'.json.gz')).get('status')=='ok' for s in US_STOCKS)
    good_funds=sum((read(folder/('info_'+a['symbol']+'.json.gz')).get('info',{}).get('totalAssets') or 0)>0 for a in ETF_DEFINITIONS)
    if good_info<18 or good_funds<len(ETF_DEFINITIONS)*.9:raise ValueError('Flow provider coverage below 90%; stop publication')

def collect_us_options(d,events,allow_download=False,fetch=None):
    """A separate optional source must not stop non-option market updates."""
    folder=d.base/'flows';rows=[]
    fetch=fetch or (lambda s:json.loads(get_bytes('https://cdn.cboe.com/api/global/delayed_quotes/options/'+s+'.json')))
    for symbol in sorted(set(US_STOCKS)|set(events)):
        dest=folder/('options_'+symbol+'.json.gz');event_dest=folder/('earnings_'+symbol+'.json.gz')
        prior=d.resource('flows/options_'+symbol+'.json.gz');old=read(prior) if prior.exists() else {}
        if not allow_download:
            rows.append(dict(symbol=symbol,status='retained_permission_required' if old.get('status')=='ok' else 'missing_permission_required',retrieved_at=old.get('retrieved_at')));continue
        if dest.exists() and (symbol not in events or event_dest.exists()):
            rows.append(dict(symbol=symbol,status='reused_current_run',retrieved_at=old.get('retrieved_at')));continue
        try:
            raw=fetch(symbol);now=pd.Timestamp.now(tz='UTC')
            # A sparse stock gamma sample can still contain a valid same-strike
            # earnings straddle. Validate these two outputs independently.
            try:out=dict(normalize(raw,symbol,now,scope=FLOW_SCOPE),status='ok')
            except ValueError:out=None
            if out and not dest.exists():save(dest,out)
            if symbol in events and not event_dest.exists():
                records=parse_contracts(raw,symbol);event=pd.Timestamp(events[symbol])
                expiries=sorted({r['expiry'] for r in records if event+pd.Timedelta(hours=1)<pd.Timestamp(r['expiry']+' 16:00',tz='America/New_York')<event+pd.Timedelta(days=15)})
                expiry=expiries[0] if expiries else None
                save(event_dest,dict(symbol=symbol,event_at=event.isoformat(),retrieved_at=now.isoformat(),provider_timestamp=raw.get('timestamp'),source='Cboe delayed option observation',spot=raw['data']['current_price'],expiry=expiry,records=[r for r in records if r['expiry']==expiry]))
            rows.append(dict(symbol=symbol,status='collected' if out else 'retained_error' if old.get('status')=='ok' else 'missing_error',retrieved_at=out['retrieved_at'] if out else old.get('retrieved_at')))
        except Exception as error:
            rows.append(dict(symbol=symbol,status='retained_error' if old.get('status')=='ok' else 'missing_error',retrieved_at=old.get('retrieved_at'),error_type=type(error).__name__))
        print('FLOW OPTIONS',symbol,rows[-1]['status'],flush=True)
        time.sleep(.6)
    report=dict(retrieved_at=pd.Timestamp.now(tz='UTC').isoformat(),automatic_access_authorized=allow_download,rows=rows)
    save(folder/'option_collection.json.gz',report)
    return report

def krx_number(v):return number(str(v).replace(',',''))

def collect_kr(d):
    dest=d.base/'flows/krx.json.gz'
    if dest.exists():return
    # Import may authenticate in this PC's build. Suppress all auth messages.
    original=requests.sessions.Session.request
    def bounded(self,method,url,**kwargs):
        kwargs.setdefault('timeout',25);return original(self,method,url,**kwargs)
    requests.sessions.Session.request=bounded
    try:
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            from pykrx import stock
            from pykrx.website.krx.etx.core import 전종목시세_ETF
            sessions=d.price('005930.KS',False).index[-5:];day=sessions[-1].strftime('%Y%m%d');start=sessions[0].strftime('%Y%m%d')
            members=sorted(d.members['kr_largecap']['members'],key=lambda r:r.get('market_cap') or 0,reverse=True)[:8]
            probe=d.base/'krx_probe.json.gz';prior=read(probe) if probe.exists() else None
            holding=pd.DataFrame(prior['hold']).set_index('티커') if prior else stock.get_exhaustion_rates_of_foreign_investment_by_ticker(day)
            stocks=[]
            for a in members:
                symbol=a['symbol'];code=symbol.split('.')[0]
                f=pd.DataFrame(prior['flows']).set_index('투자자구분') if prior and code=='005930' and start=='20260902' and day=='20260908' else stock.get_market_trading_volume_by_investor(start,day,code)
                if not {'외국인','기관합계','전체'}.issubset(f.index) or f.loc['전체','매수']<=0:raise ValueError('Missing KRX investor volume')
                stocks.append(dict(symbol=symbol,name=a['name'],from_date=start,date=day,total_volume=int(f.loc['전체','매수']),foreign_net=int(f.loc['외국인','순매수']),institution_net=int(f.loc['기관합계','순매수']),foreign_holding_pct=number(holding.loc[code,'지분율']) if code in holding.index else None))
                time.sleep(.6)
            oldday=stock.get_nearest_business_day_in_a_week(str((sessions[-1]-pd.DateOffset(months=1)).date()).replace('-',''))
            etfs=전종목시세_ETF().fetch(day);old=전종목시세_ETF().fetch(oldday);old=old.set_index('ISU_SRT_CD');rows=[]
            for _,r in etfs.iterrows():
                code=r['ISU_SRT_CD'];nav=krx_number(r['NAV']);shares=krx_number(r['LIST_SHRS']);reported=krx_number(r['INVSTASST_NETASST_TOTAMT']);prev=krx_number(old.loc[code,'NAV']) if code in old.index else None
                rows.append(dict(code=code,name=r['ISU_ABBRV'],benchmark=r['IDX_IND_NM'],nav=nav,shares=shares,reported_net_assets=reported,aum_krw=nav*shares if nav and shares else None,aum_method='NAV × listed shares',traded_value=krx_number(r['ACC_TRDVAL']),nav_1m_pct=(nav/prev-1)*100 if nav and prev else None))
            if len(rows)<500:raise ValueError('KRX ETF coverage failure')
            save(dest,dict(source='https://data.krx.co.kr/',retrieved_at=stamp(),date=day,month_base=oldday,stocks=stocks,etfs=rows))
    finally:requests.sessions.Session.request=original
    print('KRX FLOWS',len(stocks),'stocks /',len(rows),'ETFs',flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);p.add_argument('--allow-krx-auth',action='store_true');p.add_argument('--allow-cboe-download',action='store_true');p.add_argument('--market',choices=['US','KR','all'],default='all');a=p.parse_args()
    if a.market in ['KR','all'] and not a.allow_krx_auth:p.error('Existing KRX account authorization required')
    d=Data(a.as_of)
    if a.market in ['US','all']:collect_us(d,allow_cboe_download=a.allow_cboe_download)
    if a.market in ['KR','all']:collect_kr(d)
if __name__=='__main__':main()
