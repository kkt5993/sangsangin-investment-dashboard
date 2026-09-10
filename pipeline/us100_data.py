"""Weekly S&P100 membership observations from the official OEF holdings file."""
import argparse,csv,hashlib,io,re
from datetime import datetime,timezone
import pandas as pd
import requests
from .store import data_base,read_json,write_json
from .acquire import stamp

URL='https://www.ishares.com/us/products/239723/ishares-s-p-100-etf/latest-holdings.csv'
PRODUCT='https://www.ishares.com/us/products/239723/ishares-sp-100-etf'
LIMIT=1024*1024


def parse(content,as_of):
    records=list(csv.reader(io.StringIO(content.decode('utf-8-sig'))))
    if not records or records[0][0].strip()!='iShares S&P 100 ETF':raise ValueError('Unexpected holdings fund')
    header=next((i for i,r in enumerate(records) if r and r[0]=='Ticker'),None)
    if header is None:raise ValueError('Holdings header missing')
    dates=[r[1] for r in records[:header] if len(r)>1 and r[0]=='Fund Holdings as of']
    if len(dates)!=1:raise ValueError('Holdings observation date missing')
    observed=pd.Timestamp(dates[0]);cutoff=pd.Timestamp(as_of)
    if observed>cutoff or (cutoff-observed).days>14:raise ValueError('Holdings date outside accepted observation window')
    columns=records[header]
    if not set(['Ticker','Name','Sector','Asset Class','Weight (%)','Currency']).issubset(columns):raise ValueError('Holdings columns missing')
    members=[];seen=set();excluded=0
    for values in records[header+1:]:
        row=dict(zip(columns,values))
        if row.get('Asset Class')!='Equity':
            if len(values)==len(columns):excluded+=1
            continue
        ticker=row.get('Ticker','').strip();symbol={'BRKB':'BRK-B','BFB':'BF-B'}.get(ticker,ticker.replace('.','-'))
        if not re.fullmatch('[A-Z0-9-]{1,12}',symbol) or symbol in seen:raise ValueError('Invalid or duplicate equity ticker')
        if not row.get('Name') or not row.get('Sector') or row['Currency']!='USD':raise ValueError('Incomplete equity classification')
        weight=float(row['Weight (%)'].replace(',',''))
        if not 0<=weight<=100:raise ValueError('Invalid holding weight')
        seen.add(symbol)
        members.append(dict(symbol=symbol,source_ticker=ticker,name=row['Name'],market='US',sector=row['Sector'],weight_pct=weight,universe='S&P100 (OEF disclosed equities)'))
    if not 95<=len(members)<=105 or not 95<=sum(r['weight_pct'] for r in members)<=101:raise ValueError('Incomplete S&P100 equity coverage')
    return dict(as_of=str(observed.date()),members=members,excluded_non_equities=excluded)


def collect(base,as_of):
    base.mkdir(parents=True,exist_ok=True);raw=base/'oef_holdings.csv';record=base/'us100_collection.json'
    if record.exists():return read_json(record)
    checked=stamp()
    try:
        if raw.exists():content=raw.read_bytes()
        else:
            with requests.get(URL,timeout=(10,30),stream=True,headers={'Cache-Control':'no-cache'}) as response:
                response.raise_for_status();parts=[];size=0
                for part in response.iter_content(64*1024):
                    size+=len(part)
                    if size>LIMIT:raise ValueError('Holdings response exceeds 1MiB')
                    parts.append(part)
                content=b''.join(parts)
        result=parse(content,as_of)
        raw.write_bytes(content)
        result.update(source=URL,product_source=PRODUCT,retrieved_at=checked,sha256=hashlib.sha256(content).hexdigest(),raw_file=raw.name)
        write_json(base/'us100.json',result)
        status=dict(status='ok',checked_at=checked,source=URL,as_of=result['as_of'],members=len(result['members']),bytes=len(content),sha256=result['sha256'])
    except Exception as error:
        status=dict(status='error',checked_at=checked,source=URL,error_type=type(error).__name__)
    write_json(record,status);print('OEF membership',status['status'],status.get('members'),status.get('as_of'),flush=True)
    return status


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--as-of',required=True);args=p.parse_args()
    if pd.Timestamp(args.as_of).date()>datetime.now(timezone.utc).date():p.error('Future cutoff')
    collect(data_base(args.as_of),args.as_of)
