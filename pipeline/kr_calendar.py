"""Official Korean release schedules; public HTML,3annual sources, no login."""
import argparse,gzip,hashlib,re,time
from urllib.parse import urlencode
import pandas as pd
import requests
from bs4 import BeautifulSoup
from .engine import Data
from .events_data import read,save
from .store import read_json,write_json
from .acquire import budget,stamp

BOK_STATS='https://www.bok.or.kr/portal/stats/statsPublictSchdul/listCldr.do'
BOK_MEETINGS='https://www.bok.or.kr/portal/singl/crncyPolicyDrcMtg/listYear.do'
KOSTAT='https://mods.go.kr/newsPln.es?mid=a10305000000&oa_mm=ALL'

def category(name):
    for key,pattern in [('정책회의','통화정책방향'),('물가','물가'),('고용','고용|일자리|임금'),('성장·소득','국민소득|국내총생산|국민계정|가계동향|지역소득|실질 지역내총생산'),('금융·신용','통화 및 유동성|금리|대출|가계신용|자금순환|경영분석|소비자동향|기업경기'),('대외거래','국제수지|무역|투자대조표'),('생산·소비','산업활동|온라인쇼핑|서비스업|건설|운수업|소매|프랜차이즈')]:
        if re.search(pattern,name):return key
    return '기타통계'

def dated(year,month,day,label=''):
    t=pd.Timestamp(year=int(year),month=int(month),day=int(day))
    weekday=re.search(r'\(\s*([월화수목금토일])\s*\)',label)
    if weekday and '월화수목금토일'[t.dayofweek]!=weekday[1]:raise ValueError('Schedule weekday does not match date')
    return str(t.date())

def event(name,day,clock,source_id,url,agency,notes='',identity=None):
    clock=clock.strip();at=None
    if re.fullmatch(r'\d{1,2}:\d{2}',clock):at=pd.Timestamp(day+' '+clock,tz='Asia/Seoul').isoformat()
    elif clock and not re.fullmatch(r'[-—]|미정|추후.*|미표기',clock):raise ValueError('Unknown release time notation')
    identity=identity or re.sub(r'\s+','',name)
    return dict(id=source_id+':'+hashlib.sha256(identity.encode()).hexdigest()[:16],name=name,date=day,at=at,timezone='Asia/Seoul',region='KR',category=category(name),agency=agency,source_id=source_id,source=agency+' 공식 일정',url=url,notes=notes,time_status='공표시각' if at else '시각 미표기')

def unique(rows):
    if len({r['id'] for r in rows})!=len(rows):raise ValueError('Duplicate calendar identity')
    return sorted(rows,key=lambda r:(r['date'],r['at'] or '',r['name']))

def bok_statistics(content,year,url):
    soup=BeautifulSoup(content,'html.parser');tables=[t for t in soup.select('table') if t.select_one('caption') and t.select_one('caption').get_text(' ',strip=True)=='월간통계공표일정 목록']
    if len(tables)!=1:raise ValueError('BOK statistics table missing')
    out=[]
    for tr in tables[0].select('tbody tr'):
        cells=tr.find_all('td',recursive=False)
        if len(cells)!=4:raise ValueError('BOK statistics row changed')
        values=[c.get_text(' ',strip=True) for c in cells];day=pd.Timestamp(values[0]).date().isoformat()
        if not day.startswith(str(year)+'-'):raise ValueError('BOK returned another year')
        a=cells[2].select_one('[onclick]');match=re.fullmatch(r"schdulPop\('(\d+)'\)",a.get('onclick','')) if a else None
        out.append(event(values[2],day,values[1],'bok_statistics:'+str(year),url,'한국은행',values[3],match[1] if match else None))
    if not 20<=len(out)<=300:raise ValueError('BOK annual statistics coverage changed')
    return unique(out),len(out)

def bok_meetings(content,year,url):
    soup=BeautifulSoup(content,'html.parser');selected=soup.select_one('select[name="pYear"] option[selected]')
    if selected is None or selected.get('value')!=str(year):raise ValueError('BOK meeting year mismatch')
    tables=[t for t in soup.select('table') if t.select_one('caption') and '통화정책방향 회의' in t.select_one('caption').get_text(' ',strip=True)]
    if len(tables)!=1:raise ValueError('BOK policy table missing')
    out=[]
    for tr in tables[0].select('tbody tr'):
        cell=tr.select_one('th[scope="row"]');label=cell.get_text(' ',strip=True) if cell else '';match=re.fullmatch(r'(\d{1,2})월\s*(\d{1,2})일\s*\([월화수목금토일]\)',label)
        if not match:raise ValueError('BOK policy date format changed')
        day=dated(year,*match.groups(),label)
        out.append(event('한국은행 통화정책방향 결정회의',day,'','bok_meetings:'+str(year),url,'한국은행','회의 날짜이며 결정문 발표시각은 미표기',day))
    if not 1<=len(out)<=20:raise ValueError('BOK policy coverage missing')
    return unique(out),len(out)

def kostat_events(content,year,url=KOSTAT):
    soup=BeautifulSoup(content,'html.parser');heads=[h.get_text(' ',strip=True) for h in soup.select('h2,h3,h4')]
    if not any(re.fullmatch(str(year)+r'년 전체 보도계획',h) for h in heads):raise ValueError('KOSTAT annual year mismatch')
    tables=[t for t in soup.select('table') if t.select_one('caption') and '보도계획 보도일자' in t.select_one('caption').get_text(' ',strip=True)]
    if len(tables)!=1:raise ValueError('KOSTAT press table missing')
    out=[];total=0
    for tr in tables[0].select('tbody tr'):
        cells=tr.find_all('td',recursive=False)
        if len(cells)!=5:raise ValueError('KOSTAT press row changed')
        values=[c.get_text(' ',strip=True) for c in cells];total+=1
        # Statistical releases with an explicit reference year; exclude administrative news.
        if not re.match(r'^\d{4}년\s',values[2]) or re.search('기념|유공|포상|개최|교육|회의|학술',values[2]):continue
        match=re.fullmatch(r'(\d{1,2})\.(\d{1,2})\.\s*\(\s*[월화수목금토일]\s*\)',values[0])
        if not match:raise ValueError('KOSTAT release date format changed')
        day=dated(year,*match.groups(),values[0]);out.append(event(values[2],day,values[1],'kostat:'+str(year),url,'국가데이터처',values[4]))
    if not 20<=len(out)<=500:raise ValueError('KOSTAT annual statistics coverage changed')
    return unique(out),total

def raw_page(base,key,url):
    p=base/'calendar_raw'/(key+'.html.gz');meta=p.with_suffix('.meta.json')
    if p.exists() and meta.exists():
        content=gzip.decompress(p.read_bytes());m=read_json(meta)
        if hashlib.sha256(content).hexdigest()!=m['sha256']:raise ValueError('Calendar cache hash mismatch')
        return content,m
    time.sleep(.5);response=requests.get(url,timeout=25);response.raise_for_status();content=response.content
    if len(content)>1500000:raise ValueError('Calendar HTML exceeds1.5MB')
    encoded=gzip.compress(content,mtime=0);budget(len(encoded));p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(encoded)
    m=dict(url=response.url,retrieved_at=stamp(),bytes=len(content),sha256=hashlib.sha256(content).hexdigest());write_json(meta,m)
    return content,m

def collect(d,now=None):
    dest=d.base/'kr_release_calendar.json.gz'
    if dest.exists():return read(dest)
    now=pd.Timestamp(now or pd.Timestamp.now(tz='Asia/Seoul')).tz_convert('Asia/Seoul');start=str(now.date());end=str((now+pd.Timedelta(days=89)).date())
    p=d.resource('kr_release_calendar.json.gz');prior=read(p) if p.exists() else dict(items=[],sources=[])
    jobs=[]
    for year in range(now.year,pd.Timestamp(end).year+1):
        suffix='' if year==now.year else '_'+str(year)
        jobs += [('bok_statistics:'+str(year),'한국은행 통계',year,'bok_statistics'+suffix,BOK_STATS+'?'+urlencode(dict(menuNo=200775,year=year)),bok_statistics),('bok_meetings:'+str(year),'한국은행 정책회의',year,'bok_meetings'+suffix,BOK_MEETINGS+'?'+urlencode(dict(mtgSe='A',menuNo=200755,pYear=year)),bok_meetings)]
    # The observed KOSTAT annual page publishes the current year; no invented year parameter.
    jobs.append(('kostat:'+str(now.year),'국가데이터처 통계',now.year,'kostat_all',KOSTAT,kostat_events))
    items=[];sources=[]
    for id,name,year,key,url,parser in jobs:
        source=dict(id=id,name=name,year=year,url=url,checked_at=stamp(),status='error',count=0,raw_rows=0,last_success_at=None)
        try:
            content,m=raw_page(d.base,key,url);rows,total=parser(content,year,m['url'])
            items += [dict(r,observed_at=m['retrieved_at']) for r in rows]
            source.update(status='ok',count=len(rows),raw_rows=total,last_success_at=m['retrieved_at'],sha256=m['sha256'])
        except (ValueError,requests.RequestException) as e:
            fallback=[r for r in prior['items'] if r['source_id']==id];items+=fallback;old=next((r for r in prior['sources'] if r['id']==id),{})
            source.update(status='stale' if fallback else 'error',count=len(fallback),last_success_at=old.get('last_success_at'),error_type=type(e).__name__)
        sources.append(source)
    result=dict(retrieved_at=stamp(),from_date=start,to_date=end,items=unique(items),sources=sources,status='ok' if all(s['status']=='ok' for s in sources) else 'partial',note='Official scheduled dates, not actual publication confirmations. KOSTAT reference-year titles only; no administrative news. Current-year KOSTAT page only.')
    save(dest,result);return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);a=p.parse_args();r=collect(Data(a.as_of));print('KR CALENDAR',r['status'],len(r['items']),'annual events',[(s['name'],s['status']) for s in r['sources']])
if __name__=='__main__':main()
