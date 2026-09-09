"""Extract only public instrument identities from a local study; never market values."""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True);args=p.parse_args()
def read(n):return json.loads((args.reference/(n+'.json')).read_text(encoding='utf-8'))
cats=[]
for c in read('etfmon')['etf_cats']:
    cats.append(dict(id=c['key'],name=c['title'],items=[dict(symbol=r['ticker'],name=r['name'],category=c['key']) for r in c['rows']]))
stocks={}
for r in read('discovery')['discovery']['stocks']:
    stocks[r['tk']]=dict(symbol=r['tk'],name=r['name'],market=r['market'],sector=r.get('sector'))
overrides={'IFX':'IFX.DE','CSU':'CSU.TO','SUNPHARMA':'SUNPHARMA.NS','BNP':'BNP.PA','DBK':'DBK.DE','RHM':'RHM.DE','SIE':'SIE.DE','SAF':'SAF.PA','AIR':'AIR.PA','RR':'RR.L','BA':'BA.L','LT':'LT.NS','MC':'MC.PA','RMS':'RMS.PA','RELIANCE':'RELIANCE.NS','3993':'3993.HK','TTM':'TATAMOTORS.NS'}
for r in read('growth')['companies']:
    raw=r['t'];s=overrides.get(raw,raw);region=r['region']
    if raw.isdigit():
        if region=='KR':s=raw+'.KS'
        elif region=='JP':s=raw+'.T'
        elif region=='TW':s=raw+'.TW'
    stocks.setdefault(s,dict(symbol=s,name=r['name'],market=region,sector=r['sector']))
for name,data in [('etf_categories',cats),('research_stocks',list(stocks.values()))]:
    dest=ROOT/'config'/(name+'.json');dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Categories',len(cats),'ETF positions',sum(len(c['items']) for c in cats),'research stocks',len(stocks))
