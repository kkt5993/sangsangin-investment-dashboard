"""Dated topic search observations, with separately labelled local-title matches."""
import argparse,copy,hashlib,json,re,time
from datetime import datetime,timedelta,timezone,date
from urllib.parse import urlencode
import requests
from .store import ROOT,read_json
from .guru_data import read,save,resources
from .attention_data import age
from .company_news import canonical

FILE='topic_news/feeds.json.gz'
API='https://api.gdeltproject.org/api/v2/doc/doc'


def settings():return read_json(ROOT/'config/topic_news.json')['topics']


def window(as_of):
    end=date.fromisoformat(as_of)
    return (end-timedelta(days=6)).isoformat(),end.isoformat()


def search_url(spec,as_of):
    start,end=window(as_of)
    return API+'?'+urlencode(dict(query=spec['query'],mode='artlist',format='json',maxrecords=250,sort='datedesc',
                                 startdatetime=start.replace('-','')+'000000',enddatetime=end.replace('-','')+'235959'))


def normalize(blob):
    packet=json.loads(blob)
    if not isinstance(packet,dict) or not isinstance(packet.get('articles'),list):raise ValueError('GDELT article list required')
    rows={};excluded=0
    for item in packet['articles']:
        try:
            url=canonical(item['url']);stamp=datetime.strptime(item['seendate'],'%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
            title=str(item['title']).strip()
            if not title:raise ValueError('Empty title')
        except (KeyError,TypeError,ValueError):excluded+=1;continue
        row=dict(id=hashlib.sha256(url.encode()).hexdigest()[:24],url=url,title=title,time=stamp.isoformat(),time_basis='GDELT 색인 관측',
                 publisher=str(item.get('domain') or ''),language=str(item.get('language') or ''),source='GDELT DOC 2.0')
        if url not in rows or row['time']>rows[url]['time']:rows[url]=row
    return sorted(rows.values(),key=lambda r:(r['time'],r['id']),reverse=True),len(packet['articles']),excluded


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
            key=spec['id'];prior=packet['feeds'].get(key,{})
            # Reuse the query's actual window, not a different date range.
            url=search_url(spec,d.as_of)
            if prior.get('url')==url and prior.get('data_query')==spec['query'] and not prior.get('error') and 0<=age(prior.get('checked_at'),now)<24:continue
            pause(6);report['requests']+=1
            try:
                response=session.get(url,timeout=(10,30));response.raise_for_status()
                rows,count,excluded=normalize(response.content);sha=hashlib.sha256(response.content).hexdigest();raw='topic_news/raw/'+sha+'.json'
                if not d.resource(raw).exists():
                    target=d.base/raw;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(response.content)
                merged={r['url']:r for r in prior.get('items',[])} if prior.get('data_query')==spec['query'] else {}
                for row in rows:merged[row['url']]=dict(row,first_seen_at=merged.get(row['url'],{}).get('first_seen_at',now.isoformat()),last_seen_at=now.isoformat())
                packet['feeds'][key]=dict(**spec,data_query=spec['query'],url=url,items=sorted(merged.values(),key=lambda r:(r['time'],r['id']),reverse=True),
                    response_items=count,excluded_items=excluded,response_sha256=sha,checked_at=now.isoformat(),retrieved_at=now.isoformat(),error=None)
            except Exception as error:
                code=getattr(getattr(error,'response',None),'status_code',None)
                report['errors'].append(dict(id=key,type=type(error).__name__,http_status=code))
                packet['feeds'][key]=dict(prior,**spec,url=url,checked_at=now.isoformat(),error=type(error).__name__)
                if code in [401,403,429]:report['status']='access_refused';break
                if isinstance(error,requests.RequestException):report['status']='error';break
            packet['collection']=dict(report,status='error' if report['errors'] else 'ok');save(d.base/FILE,packet)
        if report['requests']:
            if report['status']!='access_refused':report['status']='error' if report['errors'] else 'ok'
            packet['collection']=report;save(d.base/FILE,packet)
    finally:
        if own:session.close()
    return report


def local_articles(d):
    """Existing RSS metadata only. Do not fetch article pages or Google results."""
    from .company_news import FILE as COMPANY
    p=d.resource(COMPANY);companies=read(p) if p.exists() else {}
    p=d.resource('news.json.gz');news=read(p) if p.exists() else {}
    rows={}
    packets=[(r.get('items',[]),r.get('retrieved_at')) for r in companies.get('feeds',{}).values()]
    packets.append((news.get('items',[]),news.get('retrieved_at')))
    for items,retrieved in packets:
        for a in items:
            try:
                url=canonical(a['url']);t=datetime.fromisoformat(a['published_at'])
                if t.tzinfo is None:continue
            except (KeyError,ValueError,TypeError):continue
            r=dict(id=hashlib.sha256(url.encode()).hexdigest()[:24],url=url,title=a['title'],time=t.astimezone(timezone.utc).isoformat(),
                   time_basis='RSS 발행',publisher=a.get('source',''),source=a.get('source',''),retrieved_at=retrieved,
                   first_seen_at=a.get('first_seen_at') or retrieved)
            if url not in rows or (retrieved or '')>(rows[url].get('retrieved_at') or ''):rows[url]=r
    return sorted(rows.values(),key=lambda r:(r['time'],r['id']),reverse=True)


def matched(title,spec):
    groups=spec.get('title_groups',[])
    evidence=[[term for term in group if re.search(r'(?<!\w)'+re.escape(term)+r'(?!\w)',title,re.I)] for group in groups]
    return sorted(set(term for group in evidence for term in group)) if evidence and all(evidence) else []


def views(d,dragon,now=None):
    from .news_tone import FILE as TONE,settings as tone_settings,annotate
    now=now or datetime.now(timezone.utc);p=d.resource(FILE);packet=read(p) if p.exists() else {};tone_path=d.resource(TONE)
    tone=read(tone_path) if tone_path.exists() else {};specification=tone_settings();start,end=window(d.as_of)
    local=[r for r in local_articles(d) if start<=r['time'][:10]<=end];items=[]
    for spec in settings():
        saved=packet.get('feeds',{}).get(spec['id'],{});valid_query=saved.get('data_query')==spec['query']
        search=[r for r in saved.get('items',[]) if valid_query and start<=r['time'][:10]<=end]
        cached=[dict(r,matched_terms=matched(r['title'],spec)) for r in local if matched(r['title'],spec)]
        fresh=valid_query and saved.get('url')==search_url(spec,d.as_of) and not saved.get('error') and 0<=age(saved.get('retrieved_at'),now)<=36
        sets={}
        for provider,articles in [('gdelt',search),('local',cached)]:
            enriched,summary=annotate(articles,tone,specification,False);summary.pop('positive_hit',None)
            sets[provider]=dict(items=enriched,count=len(enriched),tone_summary=summary,tone=summary['score'])
        items.append(dict(**spec,sets=sets,url=search_url(spec,d.as_of),available=bool(fresh),data_available=bool(valid_query and saved.get('retrieved_at')),retrieved_at=saved.get('retrieved_at'),
                          checked_at=saved.get('checked_at'),error=saved.get('error'),response_items=saved.get('response_items'),
                          capped=(saved.get('response_items') or 0)>=250,excluded_items=saved.get('excluded_items',0)))
    section=dict(type='topicnews',title='테마·국가·정책 뉴스',group='지금 주목',as_of=d.as_of,start=start,end=end,computed_at=now.isoformat(),items=items,
        collection=packet.get('collection',{}),source_vintage=p.parent.parent.name if p.exists() else None,
        tone_source_vintage=tone_path.parent.parent.name if tone_path.exists() else None,tone_collection=tone.get('collection',{}),
        note='20개 주제를 별도로 검색합니다. GDELT는 색인 관측일, 기존 RSS는 발행일을 사용해 서로 합산하지 않습니다. 기존 기사 제목 일치는 기업·정책 RSS의 제한된 표본이며 주제 전체 뉴스가 아닙니다. 검색어와 일치 근거를 확인하세요. 제목 톤은 금융 문장용 FinBERT의 참고 분류로 정치·재난 위험, 사실 여부, 기업의 호재·악재를 뜻하지 않으며 매매 신호에 합산하지 않습니다.')
    dragon['sections']=[s for s in dragon['sections'] if s['type']!='topicnews']+[section]
    dragon['missing']=[r for r in dragon.get('missing',[]) if not r.startswith('주제 뉴스:')]
    pending=sum(not r['data_available'] for r in items)
    if pending:dragon['missing'].append(f'주제 뉴스: GDELT 검색 {pending}개 주제 미확보. 기존 RSS 제목 일치는 별도 표본이며 검색 결과 확보로 세지 않습니다.')
    return dragon


def verify(section):
    import math
    from .news_tone import valid,key,text,settings as tone_settings
    definitions={r['id']:r for r in settings()};spec=tone_settings()
    assert {r['id'] for r in section['items']}==set(definitions) and len(section['items'])==len(definitions)
    assert (section['start'],section['end'])==window(section['as_of'])
    for item in section['items']:
        definition=definitions[item['id']]
        assert item['query']==definition['query'] and item['title_groups']==definition['title_groups']
        assert not item['available'] or item['data_available'] and not item['error']
        assert item['capped']==((item['response_items'] or 0)>=250)
        for provider,group in item['sets'].items():
            assert provider in ['gdelt','local'] and group['count']==len(group['items'])==len({a['url'] for a in group['items']})
            unique={}
            for article in group['items']:
                assert canonical(article['url'])==article['url'] and article['title']
                assert section['start']<=article['time'][:10]<=section['end'] and datetime.fromisoformat(article['time']).tzinfo
                assert article['time_basis']==('RSS 발행' if provider=='local' else 'GDELT 색인 관측')
                if provider=='local':assert article['matched_terms']==matched(article['title'],definition) and article['matched_terms']
                result=article['tone'];identity=key(article['title'],spec)
                if result['available']:
                    assert valid(result) and result['key']==identity and result['input_sha256']==hashlib.sha256(text(article['title']).encode()).hexdigest()
                else:assert result['reason']
                unique[identity]=result
            summary=group['tone_summary'];good=[r for r in unique.values() if r['available']]
            assert summary['total']==len(unique) and summary['classified']==len(good) and 'positive_hit' not in summary
            assert summary['available']==bool(good) and summary['model']==spec['repo'] and summary['revision']==spec['revision']
            assert summary['labels']=={label:sum(r['label']==label for r in good) for label in ['positive','negative','neutral']}
            assert summary['complete']==bool(unique and len(good)==len(unique))
            if good:
                expected=sum(r['score'] for r in good)/len(good)
                assert math.isclose(group['tone'],expected,abs_tol=1e-6) and math.isclose(summary['score'],expected,abs_tol=1e-6)
            else:assert group['tone'] is None and summary['score'] is None


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);a=p.parse_args();print(json.dumps(collect(resources(a.as_of))))
