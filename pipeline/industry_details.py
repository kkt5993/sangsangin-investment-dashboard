"""Industry P/Q/C/S cards. Official series units remain distinct from proxies."""
from .engine import *
from .pm_details import observation

# sector, label, source key, units, role, favorable direction. Reference card
# organization is retained; descriptions and calculation are independently made.
SPECS=[
 ('반도체·IT','필라델피아 반도체','^SOX','index','S','up'),
 ('반도체·IT','반도체·전자부품 생산','IPG3344S','2017=100','Q','up'),
 ('반도체·IT','반도체 제조 PPI','PCU334413334413','1998-12=100','P','up'),
 ('에너지','3-2-1 정제마진','CRACK','USD/bbl','P','up'),
 ('에너지','WTI','CL=F','USD/bbl','P','mixed'),('에너지','Henry Hub 가스','NG=F','USD/MMBtu','P','mixed'),
 ('금속·철강','구리','HG=F','USD/lb','Q','up'),('금속·철강','철강 PPI','WPU101','1982=100','P','up'),('금속·철강','금','GC=F','USD/oz','S','mixed'),
 ('조선·해운','화물운송 물동량','TSIFRGHT','2000=100','Q','up'),('조선·해운','미국 운송 ETF','IYT','USD','S','up'),('조선·해운','건화물 운임선물 ETF','BDRY','USD','P','up'),
 ('자동차','미국 자동차 판매','TOTALSA','million SAAR','Q','up'),('자동차','리튬·배터리 ETF','LIT','USD','C','mixed'),('자동차','자동차·부품 생산','IPG3361T3S','2017=100','Q','up'),
 ('부동산·건설','건축허가','PERMIT','thousand SAAR','Q','up'),('부동산·건설','주택착공','HOUST','thousand SAAR','Q','up'),('부동산·건설','30년 모기지금리','MORTGAGE30US','%','C','down'),('부동산·건설','목재 선물','LBR=F','USD/1000 board feet','C','mixed'),
 ('소비·유통','신규 실업수당','ICSA','persons','Q','down'),('소비·유통','소매판매','RSAFS','USD mn','Q','up'),('소비·유통','미시간 소비자심리','UMCSENT','1966Q1=100','Q','up'),
 ('제조·무역','제조업 신규수주','AMTMNO','USD mn','Q','up'),('제조·무역','내구재 신규수주','DGORDER','USD mn','Q','up'),('제조·무역','한국 월수출','KR_EXPORT','USD bn','Q','up'),('제조·무역','한국 기초화학 수출물량','KR_CHEM_EXPORT','2020=100','Q','up'),
 ('농업·식품','밀','ZW=F','cent/bushel','C','down'),('농업·식품','옥수수','ZC=F','cent/bushel','C','down'),('농업·식품','대두','ZS=F','cent/bushel','C','down'),
 ('금융·은행','10Y−2Y 금리차','T10Y2Y','%p','P','up'),('금융·은행','HY OAS','BAMLH0A0HYM2','%','C','down'),('금융·은행','은행 ETF','KBE','USD','S','up'),
 ('2차전지·소재','리튬·배터리 ETF','LIT','USD','Q','up'),('2차전지·소재','우라늄 ETF','URA','USD','P','up'),('2차전지·소재','소재 ETF','XLB','USD','S','up'),
 ('항공·여행','항공 ETF','JETS','USD','S','up'),('항공·여행','연료비 대용 WTI','CL=F','USD/bbl','C','down'),
 ('헬스·바이오','바이오텍 ETF','XBI','USD','S','up'),('헬스·바이오','대형 바이오 ETF','IBB','USD','S','up')]

def change(s,months,absolute=False):
    if not len(s):return None
    old=s.loc[:s.index[-1]-pd.DateOffset(months=months)]
    if not len(old):return None
    return number(s.iloc[-1]-old.iloc[-1]) if absolute else number((s.iloc[-1]/old.iloc[-1]-1)*100) if old.iloc[-1]>0 else None

def industry_views(d,obj):
    items=[]
    f=pd.concat({s:d.price(s,False) for s in ['RB=F','HO=F','CL=F']},axis=1).dropna()
    crack=(2*f['RB=F']*42+f['HO=F']*42-3*f['CL=F'])/3
    for sector,name,key,unit,role,direction in SPECS:
        s=crack if key=='CRACK' else d.mac(key) if key in d.macro else d.price(key,False)
        if key=='KR_EXPORT':
            meta_unit=d.macro_meta.get(key,{}).get('unit','')
            if meta_unit in ['천달러','천불']:s=s/1e6
            elif meta_unit in ['백만달러','백만불']:s=s/1000
            else:raise ValueError('Unknown Korean export unit')
        value,date=observation(s);tail=s.loc[s.index[-1]-pd.DateOffset(years=3):] if len(s) else s
        std=tail.std(ddof=0);z=number((tail.iloc[-1]-tail.mean())/std) if len(tail)>24 and std>0 else None
        absolute=unit in ['%','%p'] or key=='CRACK';one=change(s,1,absolute);three=change(s,3,absolute)
        signal='판정 없음' if one is None else '양면 영향' if direction=='mixed' else '보합' if abs(one)<1e-8 else '개선 방향' if (one>0)==(direction=='up') else '부담 방향'
        source='https://ecos.bok.or.kr/' if key.startswith('KR_') else 'https://fred.stlouisfed.org/series/'+key if key in d.macro else 'https://finance.yahoo.com/'
        items.append(dict(sector=sector,name=name,key=key,unit=unit,role=role,direction=direction,value=value,date=date,z=z,
            one_month=one,three_month=three,change_unit=unit if absolute else '%',signal=signal,source=source,
            spark=points(tail,60),note='ETF 가격은 해당 산업 심리의 대용이며 상품 현물가격과 다릅니다.' if key in ['LIT','BDRY','URA'] else '휘발유·난방유 선물 USD/gallon을 42배로 환산한 정제 스프레드. 실제 정유사 마진은 아닙니다.' if key=='CRACK' else '같은 지표도 생산자와 소비자에게 영향이 다를 수 있습니다.'))
    obj['sections'].append(dict(type='industry',title='산업별 핵심 지표 · 13개 산업',group='산업별 핵심지표',items=items))
    obj['method_note']+=' 산업 지표는 P=판가, Q=수요·생산, C=원가, S=시장심리로 구분합니다. 1·3개월은 달력 기준 직전 관측과 비교하고 금리·스프레드는 차이, 양수 가격·지수는 변화율을 사용합니다. z는 최근3년 관측 분포, 방향 판정은1개월 변화입니다.'
    missing=[a['name'] for a in items if a['value'] is None]
    if missing:obj['missing'].append('산업 미수집 지표: '+', '.join(missing))
