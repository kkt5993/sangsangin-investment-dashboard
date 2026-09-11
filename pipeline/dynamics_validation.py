"""Public dynamics cross-checks; does not collect or fit data."""
import math
import pandas as pd


def verify_section(s,cutoff):
    if s.get('pending'):assert s['reason'];return
    assert s['version']==2 and len(s['cost_cases'])==4
    assert s['date']<=s['price_date']<=cutoff
    recent=lambda n:(pd.Timestamp(cutoff).to_period('M')-(n-1)).start_time.strftime('%Y-%m-%d')
    for key,n,field in [('phase',36,'name'),('series',144,'date')]:
        rows=s[key];assert len(rows)<=n;dates=[r[field] for r in rows];assert dates==sorted(set(dates));assert all(recent(n)<=v<=cutoff for v in dates)
    surf=s['surface'];assert surf['windows']==[5,10,20,40,60,90,120,180];assert len(surf['dates'])<=60
    assert all(recent(60)<=t<=cutoff for t in surf['dates']) and len(surf['dates'])==len(surf['values'])
    assert all(len(row)==8 and all(x is None or math.isfinite(x) and x>=0 for x in row) for row in surf['values'])
    current=s['current'];assert 0<=current['risk']<=100 and 0<=current['exposure']<=1.5
    for r in s['series']+s['daily']:
        if r['risk'] is not None:
            value=100/(1+math.exp(-max(-50,min(50,r['z_tau']-.5*r['z_beta']-.5*r['z_alpha']))))
            assert math.isclose(r['risk'],value,abs_tol=.0001)
            expected=min(1.5,15/r['vol'])*(1-.6*r['risk']/100)
            assert math.isclose(r['exposure'],expected,rel_tol=1e-5,abs_tol=1e-5)
    chart=s['charts'][0];assert chart['guides']==[65] and chart['limits']==[0,100] and chart['shade_above']==65
    assert [a['axis'] for a in chart['series']]==['left','right']
    assert all(recent(60)<=t<=cutoff for a in chart['series'] for t,v in a['points'])
    periods=set()
    for c in s['cost_cases']:
        if not c['available']:continue
        periods.add((c['origin'],c['start'],c['end'],c['sessions']));assert c['origin']<c['start']<=c['end']<=cutoff
        assert c['sessions']==c['model']['sessions']==c['benchmark']['sessions']
        assert 0<len(c['rows'])<=252;assert len(c['chart']['series'])==2
        for a in c['chart']['series']:assert a['points'][0]==[c['origin'],100.];assert a['points'][-1][0]==c['end']
        previous=None
        for r in c['rows']:
            assert r['signal_date']<r['date']<=c['end'] and 0<=r['weight']<=1.5
            if previous:assert previous['date']==r['signal_date']
            near=lambda a,b:math.isclose(a,b,rel_tol=1e-5,abs_tol=.0001)
            assert near(r['turnover'],abs(r['weight']-r['held']))
            assert near(r['fee_pct'],r['turnover']*c['bps']/100)
            assert near(r['financing_pct'],max(r['weight']-1,0)*c['borrow_pct']/252)
            assert near(r['gross_return_pct'],r['weight']*r['asset_return_pct'])
            assert near(r['net_return_pct'],max(-100,r['gross_return_pct']-r['fee_pct']-r['financing_pct']))
            if previous:assert near(r['nav'],previous['nav']*(1+r['net_return_pct']/100))
            previous=r
        assert math.isclose(c['chart']['series'][0]['points'][-1][1],c['rows'][-1]['nav'],abs_tol=.000001)
    if not any(c['bankrupt'] for c in s['cost_cases']):assert len(periods)<=1
