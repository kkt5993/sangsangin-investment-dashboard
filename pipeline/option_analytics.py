"""Public OI gamma convention, explicitly distinct from dealer inventory."""
import numpy as np
from scipy.stats import norm
from .engine import table

def gamma(spot,strike,vol,t,rate):
    d1=(np.log(spot/strike)+(rate+.5*vol*vol)*t)/(vol*np.sqrt(t))
    return norm.pdf(d1)/(spot*vol*np.sqrt(t))

def observation_sections(p):
    scope=p.get('scope') or {};band=scope.get('strike_band')
    label=f"{scope['min_dte']}~{scope['max_dte']}일 · 행사가 ±{band*100:g}% · 공급된 범위 내 모든 만기" if p.get('scope_complete') and band is not None else '이전 제한 관측 · 7~45일 중 첫3만기 (전체 범위 미확보)'
    return [table(p['symbol']+' 옵션 관측 범위',['항목','값'],[
        ['계산 범위',label],['계산 현물 · 옵션 원자료 USD',p['spot']],['옵션 수집 시각 UTC',p['retrieved_at']],
        ['공급처 시각 · 시간대 미제공',p.get('provider_timestamp')],['참고 종가 · 계산 현물과 별개',p.get('reference_close')],['참고 종가 기준일',p['price_date']],
        ['만기',', '.join(p['expiries'])],['수집 계약 수',p['contracts']],['유효 OI 계약 수',p['valid_oi']],['유효 IV·OI 계약 수',p['valid_gamma']],
        ['Put/Call OI',p['put_call']],['합계 GEX · USD bn / 1%',p['net']],['30D 기대폭 IV 만기',p['em_expiry']],['같은 ATM 콜/풋 행사가',p['em_strike']],
        ['모형 금리 % · DGS3MO',p.get('rate')],['금리 관측일',p.get('rate_date')],['기록 상태',status_label(p.get('collection_status'))]]),
        table(p['symbol']+' 만기별 OI 집중·감마 합계',['만기','잔존 달력일 · 수집 시점','콜 OI','풋 OI','전체 유효 OI 대비 %','GEX USD bn/1%','OI 유효 계약','IV·OI 유효 계약'],[[r[k] for k in ['expiry','dte','call_oi','put_oi','oi_pct','gex','valid_oi','valid_gamma']] for r in p['maturity']])]

def status_label(status):
    return {'retained_permission_required':'기존 관측 유지 · 자동 수집 권한 확인 필요','missing_permission_required':'미확보 · 자동 수집 권한 확인 필요','retained_error':'수집 실패 · 기존 관측 유지','missing_error':'수집 실패 · 미확보','collected':'수집 완료','reused_current_run':'같은 실행 자료 재사용','preserved_observation':'보존 관측','missing':'미확보'}.get(status,'보존 관측')

def collection_section(d):
    from .wagdog import packets
    packets(d)
    return table('미국 옵션 갱신 상태',['ETF','상태','보존 자료 수집 UTC'],[[r['symbol'],status_label(r['status']),r['retrieved_at']] for r in d._option_states])

def option_sections(d):
    from .wagdog import packets
    sections=[]
    for p in packets(d):
        if p['symbol'] not in ['SPY','QQQ','IWM']:continue
        symbol=p['symbol']
        sections.append(dict(type='optionprofile',title=symbol+' · 행사가별 부호 가정 GEX',mode='gamma',**p))
        sections.append(dict(type='scatter',title=symbol+' · 가상 기초자산 가격별 감마',x_label='가상 기초자산 USD',y_label='USD bn / 1% 가격 변화',trajectory=True,points=p['curve']))
        sections+=observation_sections(p)
    sections.append(collection_section(d))
    return sections
