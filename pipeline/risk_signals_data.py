"""Small official risk inputs; preserve dates, units and revised deltas locally."""
import argparse
import contextlib
import hashlib
import io
from types import SimpleNamespace
import numpy as np
import pandas as pd
from .engine import Data
from .events_data import read,save
from .acquire import stamp

FOLDER='risk_signals/'
NEWS_URL='https://www.frbsf.org/wp-content/uploads/news_sentiment_data.xlsx'
NEWS_SOURCE='https://www.frbsf.org/research-and-insights/data-and-indicators/daily-news-sentiment-index/'
VK_NAME='코스피 200 변동성지수'
VK_BLD='dbms/MDC/STAT/standard/MDCSTAT01201'


def numeric(v):
    if v is None or isinstance(v,bool):raise ValueError('Missing numeric observation')
    x=float(str(v).replace(',',''))
    if not np.isfinite(x):raise ValueError('Non-finite observation')
    return x


def unique(rows,as_of):
    found={}
    for r in rows:
        t=pd.Timestamp(r['date'])
        if pd.isna(t) or t.tzinfo is not None or t!=t.normalize():raise ValueError('Invalid daily date')
        date=str(t.date())
        if date>as_of:raise ValueError('Future risk observation')
        row=dict(r,date=date)
        if date in found and found[date]!=row:raise ValueError('Conflicting daily risk observations')
        found[date]=row
    return sorted(found.values(),key=lambda r:r['date'])


def investor_rows(packet,as_of):
    if packet.get('market')!='KOSPI' or packet.get('unit')!='KRW' or packet.get('measure')!='net_buy' or set(packet.get('excludes',[]))!={'ETF','ETN','ELW'}:
        raise ValueError('KRX investor scope or amount unit mismatch')
    result=[]
    for r in packet['rows']:
        values=[numeric(r.get('TRDVAL'+str(i))) for i in range(1,12)]
        total=numeric(r.get('TRDVAL_TOT'))
        if any(v!=int(v) for v in values) or total!=0 or abs(sum(values))>.5:
            raise ValueError('KRX net buying amounts do not balance in won')
        result.append(dict(date=r['TRD_DD'],foreign_krw=int(values[9]),institution_krw=int(sum(values[:7])),
                           other_foreign_krw=int(values[10])))
    return unique(result,as_of)


def sentiment_rows(frame,as_of):
    if not {'date','News Sentiment'}.issubset(frame.columns):raise ValueError('FRBSF worksheet schema changed')
    out=[]
    for _,r in frame.iterrows():
        date=str(pd.Timestamp(r['date']).date())
        if date>as_of:continue
        value=numeric(r['News Sentiment'])
        # Keep the provider precision in raw JSON (save rounds numeric floats).
        out.append(dict(date=date,value=str(value)))
    rows=unique(out,as_of)
    if len(rows)<252:raise ValueError('Insufficient official sentiment history')
    return rows


def vkospi_rows(packet,as_of):
    from .kr_shortgamma_data import index_rows
    q=packet.get('query',{})
    if (packet.get('name')!=VK_NAME or packet.get('index_code')!='1300'
        or packet.get('unit')!='index_points' or packet.get('measure')!='option_implied_volatility_30d'
        or any(q.get(k)!=v for k,v in {'bld':VK_BLD,'indTpCd':'1','idxIndCd':'300'}.items())):
        raise ValueError('VKOSPI index identity or unit mismatch')
    unique([dict(r,date=r['TRD_DD']) for r in packet['rows']],as_of)
    return [dict(date=r['date'],value=r['close'],open=r['open'],high=r['high'],low=r['low'])
            for r in index_rows(packet['rows'],as_of)]


def normalized(packet,part,as_of):
    if part=='investors':return investor_rows(packet,as_of)
    if part=='vkospi':return vkospi_rows(packet,as_of)
    return unique(packet['rows'],as_of)


def history(d,part):
    found={};latest={}
    for base in d.bases:
        path=base/FOLDER/(part+'.json.gz')
        if not path.exists():continue
        p=read(path);latest=p
        rows=normalized(p,part,d.as_of)
        for row in rows:found[row['date']]=row
    return sorted(found.values(),key=lambda r:r['date']),latest


def store_delta(d,part,packet):
    # Compare against immutable parents so a same-vintage retry cannot erase
    # rows first collected in this child.
    previous,_=history(SimpleNamespace(as_of=d.as_of,bases=[b for b in d.bases if b!=d.base]),part)
    prior={r['date']:r for r in previous}
    rows=normalized(packet,part,d.as_of)
    if not rows:raise ValueError('Empty risk collection')
    changed={r['date'] for r in rows if prior.get(r['date'])!=r}
    key='TRD_DD' if part in ['investors','vkospi'] else 'date'
    packet=dict(packet,observed_through=rows[-1]['date'],rows=[r for r in packet['rows'] if str(pd.Timestamp(r[key]).date()) in changed])
    save(d.base/FOLDER/(part+'.json.gz'),packet)
    return dict(part=part,status='collected',changed=len(packet['rows']),date=rows[-1]['date'],retrieved_at=packet['retrieved_at'])


def fetch_vk(d,start,end):
    """Resolve the named official index monthly, then use its observed query."""
    from urllib.parse import quote
    from bs4 import BeautifulSoup
    from pykrx.website.comm.webio import get_session
    auth=get_session();path=d.resource(FOLDER+'vkospi_definition.json.gz')
    definition=read(path) if path.exists() else {}
    fresh=definition and pd.Timedelta(0)<=pd.Timestamp(stamp())-pd.Timestamp(definition['retrieved_at'])<pd.Timedelta(days=30)
    if not fresh:
        r=auth.session.get('https://data.krx.co.kr/comm/finder/autocomplete.jspx',
            params=dict(contextName='finder_drvetcidx',value=quote('변동성'),viewCount=5,
                        bldPath='/dbms/comm/finder/finder_drvetcidx_autocomplete'),headers=auth.get_headers(),timeout=25)
        r.raise_for_status()
        if len(r.content)>64*1024:raise ValueError('Unexpected KRX finder response')
        rows=[dict(name=x.get('data-nm'),indTpCd=x.get('data-cd'),idxIndCd=x.get('data-tp'))
              for x in BeautifulSoup(r.text,'html.parser').select('li') if x.get('data-nm')==VK_NAME]
        if rows!=[dict(name=VK_NAME,indTpCd='1',idxIndCd='300')]:raise ValueError('Official VKOSPI identity changed')
        definition=dict(rows[0],retrieved_at=stamp(),source='https://data.krx.co.kr/')
        save(d.base/FOLDER/'vkospi_definition.json.gz',definition)
    if any(definition.get(k)!=v for k,v in dict(name=VK_NAME,indTpCd='1',idxIndCd='300').items()):
        raise ValueError('Invalid cached VKOSPI definition')
    r=auth.session.post('https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd',
        data=dict(bld=VK_BLD,locale='ko_KR',indTpCd='1',idxIndCd='300',strtDd=start,endDd=end),
        headers=auth.get_headers(),timeout=25)
    r.raise_for_status()
    if len(r.content)>1024**2:raise ValueError('Unexpected KRX index response')
    return r.json()['output']


def collect(d,allow_krx_auth=False,fetch_news=None,fetch_investors=None,fetch_vkospi=None):
    import requests
    reports=[];now=pd.Timestamp(stamp())
    news,meta=history(d,'sentiment');dest=d.base/FOLDER/'sentiment.json.gz'
    fresh=meta and pd.Timedelta(0)<=now-pd.Timestamp(meta['retrieved_at'])<pd.Timedelta(days=7)
    if dest.exists() or fresh:
        reports.append(dict(part='sentiment',status='reused',retrieved_at=meta.get('retrieved_at')))
    else:
        try:
            if fetch_news:blob=fetch_news()
            else:
                with requests.get(NEWS_URL,timeout=30,stream=True) as response:
                    response.raise_for_status();chunks=[];size=0
                    for chunk in response.iter_content(64*1024):
                        size+=len(chunk)
                        if size>2*1024**2:raise ValueError('Unexpectedly large sentiment workbook')
                        chunks.append(chunk)
                    blob=b''.join(chunks)
            if len(blob)>2*1024**2:raise ValueError('Unexpectedly large sentiment workbook')
            rows=sentiment_rows(pd.read_excel(io.BytesIO(blob),sheet_name='Data'),d.as_of)
            # The dashboard needs a trailing 252-observation position. Keep
            # three years of source observations, not another full history copy.
            cutoff=str((pd.Timestamp(d.as_of)-pd.DateOffset(years=3)).date())
            packet=dict(source=NEWS_SOURCE,download_url=NEWS_URL,retrieved_at=stamp(),unit='index',
                requested_as_of=d.as_of,download_sha256=hashlib.sha256(blob).hexdigest(),
                rows=[r for r in rows if r['date']>=cutoff])
            reports.append(store_delta(d,'sentiment',packet))
        except Exception as e:
            reports.append(dict(part='sentiment',status='retained_error' if news else 'missing_error',error_type=type(e).__name__,retrieved_at=meta.get('retrieved_at')))
    previous,meta=history(d,'investors');expected=str(d.price('^KS11',False).index[-1].date())
    if (d.base/FOLDER/'investors.json.gz').exists() or previous and previous[-1]['date']==expected:
        reports.append(dict(part='investors',status='reused',retrieved_at=meta.get('retrieved_at')))
    elif not allow_krx_auth:
        reports.append(dict(part='investors',status='retained_permission_required' if previous else 'missing_permission_required',retrieved_at=meta.get('retrieved_at')))
    else:
        start=(pd.Timestamp(previous[-1]['date'])-pd.Timedelta(days=10) if previous else pd.Timestamp(d.as_of)-pd.DateOffset(years=1)).strftime('%Y%m%d')
        original=requests.sessions.Session.request
        def bounded(self,method,url,**kwargs):
            kwargs.setdefault('timeout',25);return original(self,method,url,**kwargs)
        requests.sessions.Session.request=bounded
        try:
            # This installation may authenticate at import. Never expose its logs.
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                if fetch_investors:rows=fetch_investors(start,d.as_of.replace('-',''))
                else:
                    from pykrx.website.krx.market.core import 투자자별_거래실적_전체시장_일별추이_상세
                    rows=투자자별_거래실적_전체시장_일별추이_상세().fetch(start,d.as_of.replace('-',''),'STK','','','',2,3).to_dict('records')
            packet=dict(source='https://data.krx.co.kr/',retrieved_at=stamp(),requested_as_of=d.as_of,
                market='KOSPI',unit='KRW',measure='net_buy',excludes=['ETF','ETN','ELW'],rows=rows)
            normalized=investor_rows(packet,d.as_of)
            if not normalized or normalized[-1]['date']!=expected:raise ValueError('KRX investor date differs from latest KOSPI session')
            reports.append(store_delta(d,'investors',packet))
        except Exception as e:
            reports.append(dict(part='investors',status='retained_error' if previous else 'missing_error',error_type=type(e).__name__,retrieved_at=meta.get('retrieved_at')))
        finally:requests.sessions.Session.request=original
    previous,meta=history(d,'vkospi')
    if (d.base/FOLDER/'vkospi.json.gz').exists() or previous and previous[-1]['date']==expected:
        reports.append(dict(part='vkospi',status='reused',retrieved_at=meta.get('retrieved_at')))
    elif not allow_krx_auth:
        reports.append(dict(part='vkospi',status='retained_permission_required' if previous else 'missing_permission_required',retrieved_at=meta.get('retrieved_at')))
    else:
        start=(pd.Timestamp(previous[-1]['date'])-pd.Timedelta(days=10) if previous else pd.Timestamp(d.as_of)-pd.DateOffset(years=1)).strftime('%Y%m%d')
        original=requests.sessions.Session.request
        def bounded(self,method,url,**kwargs):
            kwargs.setdefault('timeout',25);return original(self,method,url,**kwargs)
        requests.sessions.Session.request=bounded
        try:
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                rows=fetch_vkospi(start,d.as_of.replace('-','')) if fetch_vkospi else fetch_vk(d,start,d.as_of.replace('-',''))
            packet=dict(source='https://data.krx.co.kr/',retrieved_at=stamp(),requested_as_of=d.as_of,
                name=VK_NAME,index_code='1300',unit='index_points',measure='option_implied_volatility_30d',
                query=dict(bld=VK_BLD,indTpCd='1',idxIndCd='300',strtDd=start,endDd=d.as_of.replace('-','')),rows=rows)
            normalized_rows=vkospi_rows(packet,d.as_of)
            if not normalized_rows or normalized_rows[-1]['date']!=expected:raise ValueError('VKOSPI date differs from latest KOSPI session')
            reports.append(store_delta(d,'vkospi',packet))
        except Exception as e:
            reports.append(dict(part='vkospi',status='retained_error' if previous else 'missing_error',error_type=type(e).__name__,retrieved_at=meta.get('retrieved_at')))
        finally:requests.sessions.Session.request=original
    result=dict(retrieved_at=stamp(),requested_as_of=d.as_of,parts=reports)
    save(d.base/FOLDER/'collection.json.gz',result)
    print('Risk inputs',[(r['part'],r['status']) for r in reports],flush=True)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);p.add_argument('--allow-krx-auth',action='store_true');a=p.parse_args()
    collect(Data(a.as_of),allow_krx_auth=a.allow_krx_auth)


if __name__=='__main__':main()
