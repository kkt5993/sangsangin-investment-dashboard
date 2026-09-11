"""Cross-check public quantitative ledgers, definitions and chart series."""
import math

def verify_quant(d):
    s=d['screen'];stocks=s['stocks'];pairs=s['pairs'];sections=d['sections'];near=lambda a,b:math.isclose(a,b,abs_tol=2e-5)
    assert s['universe']==len(stocks)==len({r['symbol'] for r in stocks})
    assert s['factor_pass']==sum(not r['excluded'] for r in stocks)
    assert s['pair_tested']==s['pair_universe']*(s['pair_universe']-1)//2
    assert len(pairs)<=10 and len(pairs)<=s['hurst_pass']<=s['correlation_pass']<=s['pair_tested']
    assert s['calendar_end']<=d['as_of']
    for r in stocks:
        if r['excluded']:assert r['factor'] is None and not r['components']
        else:
            assert len(r['components'])==8 and near(r['factor'],sum(c['contribution'] for c in r['components']))
            assert r['date']<=d['as_of'] and r['price_observations']>=220 and r['return_observations']>=218
            for c in r['components']:
                z=max(-2.5,min(2.5,(c['raw']-float(c['mean_exact']))/float(c['std_exact']))) if float(c['std_exact']) else 0.
                assert near(c['z'],z) and near(c['contribution'],c['z']*c['weight']*c['sign'])
    charts=[c for c in sections if c['type']=='line' and c['group']=='Stat Arb']
    assert len(charts)==len(pairs)
    for r,c in zip(pairs,charts):
        assert .5<=r['corr']<=.95 and r['hurst']<.5 and 450<=r['observations']<=504
        assert r['start']<r['end']<=d['as_of'] and near(r['z'],(float(r['ratio_exact'])-float(r['mean_exact']))/float(r['std_exact']))
        assert c['guides']==[-2,0,2] and len(c['series'])==1 and c['left']=='z-score'
        assert c['series'][0]['points'][-1]==[r['end'],r['z']]
        assert 220<=len(c['series'][0]['points'])<=252
    for c in sections:
        if c['type']=='quantledger':
            assert all(len(r)==len(c['columns']) for r in c['rows'])
            assert not c['detail'] or len(c['detail'])==len(c['rows'])
            for a in c['detail']:assert all(len(r)==len(a['columns']) for r in a['rows'])
    b=s['bab'];assert b['complete']==all(l['available'] for l in b['legs'])
    if b['complete']:assert near(b['net_beta'],0)
    else:assert b['net_beta'] is None
    for l in b['legs']:
        assert l['count']==len(l['rows'])
        if l['available']:
            assert near(sum(r['weight']/100*r['beta'] for r in l['rows']),1 if l['side']=='LONG' else -1)
            assert near(l['gross'],sum(abs(r['weight']) for r in l['rows']))
    assert len(s['tsmom'])==12 and sum(r['reference_named'] for r in s['tsmom'])==6
    for r in s['tsmom']:
        if r['available']:
            assert r['start12']<r['start3']<r['date']<=d['as_of']
            if r['kind']=='금리수준':assert r['exposure'] is None
            else:assert abs(r['exposure'])<=2 and near(r['exposure'],r['signal']*min(2,10/r['vol']))
    assert [r['symbol'] for r in sorted(stocks,key=lambda r:(-abs(r.get('reversal_z') or 0),r['symbol'])) if r.get('reversal_z') is not None and ((r['mom12_1']>20 and r['reversal_z']< -1.2) or (r['mom12_1']< -20 and r['reversal_z']>1.2))]==s['reversal']
    bars=[c for c in sections if c['type']=='bars'];assert [c['group'] for c in bars]==['멀티팩터','BAB','TSMOM']
    assert len(bars[0]['rows'])==min(15,s['factor_pass'])
    assert len(bars[1]['rows'])==sum(l['count'] for l in b['legs'])
    assert len(bars[2]['rows'])==sum(r['available'] for r in s['tsmom'])
