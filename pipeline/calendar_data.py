"""Official scheduled releases, separately dated from market observations."""
import argparse,re,time
from urllib.parse import urljoin
import pandas as pd
import requests
from bs4 import BeautifulSoup
from .store import data_base
from .events_data import save,read
from .acquire import stamp,get_bytes

RELEASES={'10':'BLS CPI','50':'BLS Employment','46':'BLS PPI','192':'BLS JOLTS','180':'DOL Claims','9':'Census Retail Sales','13':'Fed Industrial Production','27':'Census Housing'}

def fred_events(content,url):
    soup=BeautifulSoup(content,'html.parser');out=[];day=None;clock=None
    for row in soup.select('tr'):
        text=row.get_text(' ',strip=True);a=row.select_one('a[href^="/release?rid="]')
        if not a:
            m=re.match(r'^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) (\w+ \d+, \d{4})',text)
            if m:day=pd.Timestamp(m[2]).date();clock=None
            continue
        if day is None:continue
        cells=row.select('td');value=cells[0].get_text(' ',strip=True)
        if value:clock=value
        at=pd.Timestamp(str(day)+' '+clock,tz='America/Chicago').isoformat() if clock and clock!='N/A' else None
        out.append(dict(name=a.get_text(' ',strip=True),date=str(day),at=at,source='FRED 발표 달력',url=urljoin(url,a['href'])))
    return out

def bea_events(content,url,year):
    soup=BeautifulSoup(content,'html.parser');out=[]
    for row in soup.select('tr'):
        date=row.select_one('.release-date');title=row.select_one('.release-title');clock=row.select_one('small')
        if date is None or title is None:continue
        # The official schedule groups each table by year.
        table=row.find_parent('table');header=table.select_one('thead') if table else None
        found=re.search(r'\b20\d{2}\b',header.get_text(' ',strip=True)) if header else None
        yr=found.group() if found else str(year)
        value=date.get_text(' ',strip=True)+' '+yr
        try:
            day=pd.Timestamp(value).date();at=pd.Timestamp(value+' '+clock.get_text(' ',strip=True),tz='America/New_York').isoformat() if clock else None
        except ValueError:continue
        out.append(dict(name=title.get_text(' ',strip=True),date=str(day),at=at,source='BEA 공식 발표 일정',url=url))
    return out

def collect(base):
    dest=base/'release_calendar.json.gz'
    if dest.exists():return
    now=pd.Timestamp.now(tz='UTC');start=str(now.date());end=str((now+pd.Timedelta(days=90)).date());items=[];sources=[]
    for rid,name in RELEASES.items():
        url='https://fred.stlouisfed.org/releases/calendar'
        try:
            response=requests.get(url,params=dict(rid=rid,vs=start,ve=end,ob='rd'),timeout=25);response.raise_for_status()
            rows=fred_events(response.text,response.url)
            if not rows or len(rows)>30:raise ValueError('Unexpected release calendar coverage')
            items+=rows;sources.append(dict(name=name,status='ok',count=len(rows),url=response.url))
        except Exception as e:sources.append(dict(name=name,status='error',count=0,error_type=type(e).__name__,url=url))
        print('CALENDAR',name,sources[-1]['status'],sources[-1]['count'],flush=True);time.sleep(.5)
    url='https://www.bea.gov/news/schedule'
    try:
        probe=base/'bea_calendar_probe.json.gz';content=read(probe)['content'] if probe.exists() else get_bytes(url).decode('utf-8')
        rows=bea_events(content,url,now.year);items+=rows;sources.append(dict(name='BEA',status='ok',count=len(rows),url=url))
    except Exception as e:sources.append(dict(name='BEA',status='error',count=0,error_type=type(e).__name__,url=url))
    items={ (r['date'],r['name']):r for r in items if start<=r['date']<=end }
    if sum(s['status']=='ok' for s in sources)<7:raise ValueError('Official calendar coverage incomplete; publication stopped')
    save(dest,dict(retrieved_at=stamp(),from_date=start,to_date=end,items=sorted(items.values(),key=lambda r:(r['date'],r['at'] or '',r['name'])),sources=sources))

def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',required=True);a=p.parse_args();collect(data_base(a.as_of))
if __name__=='__main__':main()
