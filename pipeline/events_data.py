"""Bounded public event, estimate-revision and official RSS collection."""
import argparse,contextlib,gzip,io,json,time,logging
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET
import pandas as pd
import requests,yfinance as yf
from .engine import Data,clean_json
from .acquire import budget,stamp

FEEDS=[('Federal Reserve','https://www.federalreserve.gov/feeds/press_all.xml'),
       ('ECB','https://www.ecb.europa.eu/rss/press.html'),('BIS','https://www.bis.org/doclist/all_pressrels.rss'),
       ('WTO','https://www.wto.org/library/rss/latest_news_e.xml'),('IMF','https://www.imf.org/en/News/RSS'),
       ('BBC World','https://feeds.bbci.co.uk/news/world/rss.xml'),('DW','https://rss.dw.com/rdf/rss-en-all')]
def save(path,data):
    encoded=gzip.compress(json.dumps(clean_json(data),ensure_ascii=False,allow_nan=False).encode(),mtime=0)
    budget(len(encoded));path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_bytes(encoded);tmp.replace(path)

def read(path):return json.loads(gzip.decompress(path.read_bytes()))

def parse_feed(blob,source):
    """RSS2, RDF/RSS1 and Atom; accept only dated HTTPS headline links."""
    root=ET.fromstring(blob);rows=[]
    local=lambda tag:tag.rsplit('}',1)[-1]
    for item in [e for e in root.iter() if local(e.tag) in ['item','entry']][:60]:
        fields={local(e.tag):e for e in item};value=lambda k:''.join(fields[k].itertext()).strip() if k in fields else ''
        title=value('title');link=value('link')
        if not link:
            links=[e for e in item if local(e.tag)=='link' and e.attrib.get('rel','alternate')=='alternate']
            link=links[0].attrib.get('href','') if links else ''
        date=value('pubDate') or value('published') or value('date') or value('updated')
        try:
            try:t=parsedate_to_datetime(date)
            except (ValueError,TypeError):t=pd.Timestamp(date)
            t=pd.Timestamp(t)
            if pd.isna(t) or t.tzinfo is None:continue
        except (ValueError,TypeError,OverflowError):continue
        if title and link.startswith('https://'):rows.append(dict(title=title,url=link,published_at=t.isoformat(),source=source))
    return rows

def collect_events(d,limit=60):
    folder=d.base/'events';folder.mkdir(parents=True,exist_ok=True)
    symbols=sorted([s for s,a in d.fund.items() if a.get('info',{}).get('country')=='United States' and s in d.frames],key=lambda s:d.fund[s]['info'].get('marketCap') or 0,reverse=True)[:limit]
    logging.getLogger('yfinance').setLevel(logging.CRITICAL)
    for i,s in enumerate(symbols):
        file=folder/(s+'.json.gz')
        if file.exists():continue
        out=dict(symbol=s,retrieved_at=stamp(),source='Yahoo Finance event/holdings API',status='ok',errors=[])
        t=yf.Ticker(s)
        for name,fn in [('earnings_dates',lambda:t.get_earnings_dates(limit=24)),('insider',t.get_insider_transactions),('eps_revisions',t.get_eps_revisions),('eps_trend',t.get_eps_trend)]:
            try:
                with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):f=fn()
                out[name]=json.loads(f.to_json(orient='split',date_format='iso')) if f is not None and len(f) else None
            except Exception as e:out[name]=None;out['errors'].append(name+':'+type(e).__name__)
        save(file,out);print('EVENT',i+1,len(symbols),s,flush=True);time.sleep(.7)
    return len(symbols)

def collect_news(d):
    dest=d.base/'news.json.gz'
    if dest.exists():return
    items=[];sources=[]
    for source,url in FEEDS:
        try:
            r=requests.get(url,timeout=20);r.raise_for_status();parsed=parse_feed(r.content,source);items.extend(parsed);count=len(parsed)
            sources.append(dict(name=source,url=url,status='ok' if count else 'empty',items=count))
        except Exception as e:sources.append(dict(name=source,url=url,status='error',error_type=type(e).__name__))
        time.sleep(.5)
    unique={r['url']:r for r in items};items=sorted(unique.values(),key=lambda r:pd.Timestamp(r['published_at']),reverse=True)
    save(dest,dict(retrieved_at=stamp(),items=items,sources=sources));print('NEWS',len(items),'items',flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);p.add_argument('--limit',type=int,default=60);a=p.parse_args();d=Data(a.as_of)
    collect_news(d);collect_events(d,a.limit)
if __name__=='__main__':main()
