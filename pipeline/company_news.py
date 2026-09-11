"""Dated company RSS observations, local archives and request caching."""
import argparse,copy,hashlib,time
from datetime import datetime,timedelta,timezone,date
from urllib.parse import urlencode,urlsplit,urlunsplit,parse_qsl
import xml.etree.ElementTree as ET
import requests
from .store import ROOT,read_json
from .events_data import parse_feed
from .guru_data import read,save,resources
from .attention_data import age

FILE='company_news/feeds.json.gz'
SOURCE='Yahoo Finance RSS'


def settings():return read_json(ROOT/'config/company_news.json')['companies']
def feed_url(symbol):return 'https://finance.yahoo.com/rss/headline?'+urlencode(dict(s=symbol,region='US',lang='en-US'))


def canonical(url):
    u=urlsplit(url)
    if u.scheme!='https' or not u.hostname or u.username or u.password:raise ValueError('Dated HTTPS article URL required')
    query=[(k,v) for k,v in parse_qsl(u.query,keep_blank_values=True) if k!='.tsrc' and not k.startswith('utm_')]
    return urlunsplit((u.scheme,u.netloc,u.path,urlencode(query),'')).rstrip('?')


def normalize(blob):
    if b'<!DOCTYPE' in blob.upper() or b'<!ENTITY' in blob.upper():raise ValueError('XML declarations unsupported')
    root=ET.fromstring(blob)
    if root.tag.rsplit('}',1)[-1] not in ['rss','RDF','feed']:raise ValueError('RSS or Atom required')
    rows={}
    for r in parse_feed(blob,SOURCE,limit=None):
        url=canonical(r['url']);published=datetime.fromisoformat(r['published_at']).astimezone(timezone.utc).isoformat()
        rows[url]=dict(id=hashlib.sha256(url.encode()).hexdigest()[:24],url=url,title=r['title'],published_at=published,source=SOURCE)
    if not rows and any(e.tag.rsplit('}',1)[-1] in ['item','entry'] for e in root.iter()):raise ValueError('Feed entries have no valid dated articles')
    return sorted(rows.values(),key=lambda r:(r['published_at'],r['id']),reverse=True)


def collect(d,session=None,now=None,pause=time.sleep):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError('Timezone required')
    path=d.resource(FILE);packet=read(path) if path.exists() else {'feeds':{}}
    report=dict(attempted_at=now.isoformat(),status='reused',requests=0,errors=[])
    previous=packet.get('collection',{})
    if previous.get('status') in ['error','access_refused'] and 0<=age(previous.get('attempted_at'),now)<1:return dict(report,status='backoff')
    packet=copy.deepcopy(packet);own=session is None;session=session or requests.Session()
    try:
        for spec in settings():
            symbol=spec['symbol'];prior=packet['feeds'].get(symbol,{})
            if prior.get('url')==feed_url(symbol) and not prior.get('error') and 0<=age(prior.get('checked_at'),now)<24:continue
            report['requests']+=1;pause(1)
            try:
                response=session.get(feed_url(symbol),timeout=(10,30),headers={'User-Agent':'SangsanginResearch/1.0 (+https://github.com/kkt5993/sangsangin-investment-dashboard)'})
                response.raise_for_status();rows=normalize(response.content)
                digest=hashlib.sha256(response.content).hexdigest();raw='company_news/raw/'+digest+'.xml'
                if not d.resource(raw).exists():
                    target=d.base/raw;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(response.content)
                merged={r['url']:r for r in prior.get('items',[])}
                for r in rows:merged[r['url']]=dict(r,first_seen_at=merged.get(r['url'],{}).get('first_seen_at',now.isoformat()),last_seen_at=now.isoformat())
                packet['feeds'][symbol]=dict(**spec,url=feed_url(symbol),items=sorted(merged.values(),key=lambda r:(r['published_at'],r['id']),reverse=True),
                    response_items=len(rows),response_sha256=digest,checked_at=now.isoformat(),retrieved_at=now.isoformat(),error=None)
            except Exception as exc:
                code=getattr(getattr(exc,'response',None),'status_code',None)
                report['errors'].append(dict(symbol=symbol,type=type(exc).__name__,http_status=code))
                packet['feeds'][symbol]=dict(prior,**spec,url=feed_url(symbol),checked_at=now.isoformat(),error=type(exc).__name__)
                if code in [401,403,429]:report['status']='access_refused';break
        if report['requests']:
            if report['status']!='access_refused':report['status']='error' if report['errors'] else 'ok'
            packet['collection']=report;save(d.base/FILE,packet)
    finally:
        if own:session.close()
    return report


def views(d,dragon,now=None):
    now=now or datetime.now(timezone.utc);path=d.resource(FILE);raw=read(path) if path.exists() else {}
    from .news_tone import FILE as TONE_FILE,settings as tone_settings,annotate
    tone_path=d.resource(TONE_FILE);tone_packet=read(tone_path) if tone_path.exists() else {};tone_spec=tone_settings()
    start=(date.fromisoformat(d.as_of)-timedelta(days=6)).isoformat();items=[]
    entity_section=next(s for s in dragon['sections'] if s['type']=='entities');entities={e['symbol']:e for e in entity_section['entities']}
    for e in entities.values():e.pop('company_news',None)
    for spec in settings():
        r=raw.get('feeds',{}).get(spec['symbol'],{})
        rows=[a for a in r.get('items',[]) if start<=a['published_at'][:10]<=d.as_of]
        fresh=r.get('url')==feed_url(spec['symbol']) and bool(r.get('retrieved_at')) and not r.get('error') and 0<=age(r.get('retrieved_at'),now)<=36
        rows,tone=annotate(rows,tone_packet,tone_spec,fresh)
        item=dict(**spec,entity=entities.get(spec['symbol'],{}).get('id'),url=feed_url(spec['symbol']),source=SOURCE,
            start=start,end=d.as_of,latest=max([a['published_at'] for a in rows],default=None),observed_count=len(rows),volume_hit=fresh and len(rows)>=8,
            available=fresh,retrieved_at=r.get('retrieved_at'),checked_at=r.get('checked_at'),error=r.get('error'),response_items=r.get('response_items'),
            items=rows,excluded_after_cutoff=sum(a['published_at'][:10]>d.as_of for a in r.get('items',[])),tone=tone['score'],tone_summary=tone)
        items.append(item)
        if spec['symbol'] in entities:entities[spec['symbol']]['company_news']=item
    section=dict(type='companynews',title='기업 뉴스 · 피드 관측',group='지금 주목',as_of=d.as_of,computed_at=now.isoformat(),source_vintage=path.parent.parent.name if path.exists() else None,
        collection=raw.get('collection',{}),tone_collection=tone_packet.get('collection',{}),tone_source_vintage=tone_path.parent.parent.name if tone_path.exists() else None,items=items,settings=dict(days=7,volume_threshold=8,cache_hours=24,fresh_hours=36),
        note='기업별 Yahoo Finance RSS가 연결한 기사 표본입니다. UTC 발행일 기준 최근7일·가격 기준일 이하만 집계합니다. 전체 뉴스량·기업만 단독으로 다룬 기사 수가 아니며 누적 수집 시작 전의 뉴스는 빠질 수 있습니다. 제목·발행일·원문과 피드 연결을 확인하세요. FinBERT는 연결된 영문 제목 전체의 톤을 분류하며 개별 기업의 호재·악재나 수익률을 판정하지 않습니다. 기사8건 규칙과 제목 톤 양수 규칙을 구분합니다.')
    dragon['sections']=[s for s in dragon['sections'] if s['type']!='companynews']+[section]
    return dragon


if __name__=='__main__':
    import json
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);a=p.parse_args();print(json.dumps(collect(resources(a.as_of))))
