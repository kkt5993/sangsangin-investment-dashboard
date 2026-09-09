"""Pure, offline calculations. All percentages are 100 * decimal returns.

The chosen conventions are explicit team parameters, not recovered backend code.
No forward fill; pair observations use the intersection of completed sessions.
"""
import numpy as np
import pandas as pd

PARAMETERS = dict(version='prices-v1', return_sessions={'1W':5, '1M':21, '3M':63, '6M':126, '1Y':252},
                  z_window=1260, z_min_periods=1260, z_ddof=0,
                  chart_years=5, momentum_chart_months=[3,6],
                  max_staleness_calendar_days=7,
                  price={'KR_ETF':'Yahoo Adj Close','US_ETF':'Yahoo Close (dividends excluded)', 'index_crypto':'Yahoo Close'},
                  alignment='pairwise intersection; no fill; completed date only',
                  momentum_curve='100 * ((A/A0)/(B/B0) - 1)',
                  band_levels=[-2,-1,0,1,2], bar_extreme_markers=[-2.58,2.58])


def finite(value):
    return float(value) if pd.notna(value) and np.isfinite(value) else None


def clean(s, as_of):
    s = s.loc[:as_of].dropna().astype(float)
    if not s.index.is_unique or not s.index.is_monotonic_increasing or (s <= 0).any():
        raise ValueError('Prices must have unique ordered dates and positive values')
    return s


def align(a, b, as_of):
    return pd.concat([clean(a,as_of).rename('a'), clean(b,as_of).rename('b')], axis=1, join='inner').dropna()


def trailing_return(s, sessions):
    if len(s) <= sessions:
        return None
    return finite(100 * (s.iloc[-1] / s.iloc[-sessions-1] - 1))


def ytd_return(s):
    if s.empty:
        return None
    before = s[s.index < pd.Timestamp(s.index[-1].year,1,1)]
    return finite(100 * (s.iloc[-1]/before.iloc[-1]-1)) if len(before) else None


def relative_strength(frame, window=1260, lag=63, ddof=0):
    spread = 100 * (frame.a.pct_change(lag, fill_method=None)-frame.b.pct_change(lag, fill_method=None))
    roll = spread.rolling(window, min_periods=window)
    std = roll.std(ddof=ddof)
    z = (spread-roll.mean()) / std.where(std > 1e-10)
    return pd.DataFrame({'spread_pp':spread, 'z':z, 'dz_1w':z-z.shift(5)})


def zone(z):
    if z is None:
        return '산출 불가'
    if z >= 2:
        return '과열'
    if z >= 1:
        return '강세'
    if z <= -2:
        return '과매도'
    if z <= -1:
        return '약세'
    return '중립'


def cumulative_excess(frame, months):
    """Calendar horizon; last common close on/before the cutoff is the base."""
    if frame.empty:
        return pd.Series(dtype=float), None
    cutoff = frame.index[-1] - pd.DateOffset(months=months)
    prior = frame[frame.index <= cutoff]
    if prior.empty:
        return pd.Series(dtype=float), None
    sample = frame.loc[prior.index[-1]:]
    ratio = sample.a/sample.b
    return 100*(ratio/ratio.iloc[0]-1), str(sample.index[0].date())


def stock_ranking(prices, members, as_of):
    """Optional explicit universe. Never interpret today's members as historical PIT.

    members: [{symbol,name}]. Weighted 3/6/9/12 month cumulative returns,
    40/20/20/20 weights; original backend weights/universe are unverified.
    """
    rows = []
    for m in members:
        if m['symbol'] not in prices:
            continue
        s = clean(prices[m['symbol']], as_of)
        if s.empty or (pd.Timestamp(as_of)-s.index[-1]).days > 7:
            continue
        r = {str(n):trailing_return(s,n) for n in [5,21,63,126,189,252]}
        score = sum(r[str(n)]*w for n,w in [(63,.4),(126,.2),(189,.2),(252,.2)]) if all(r[str(n)] is not None for n in [63,126,189,252]) else None
        rows.append(dict(**m, ret_1w=r['5'], ret_1m=r['21'], ytd=ytd_return(s), score=score))
    valid = [r for r in rows if r['score'] is not None]
    scores = pd.Series([r['score'] for r in valid])
    ranks = 1 + 98*(scores.rank(method='average')-1)/max(1,len(valid)-1)
    for r,rank in zip(valid,ranks):
        r['rs_rating'] = int(round(rank))
    weekly = sorted([r for r in rows if r['ret_1w'] is not None], key=lambda r:r['ret_1w'], reverse=True)
    return dict(eligible=len(valid), observed=len(rows), requested=len(members),
                strong=weekly[:8], weak=sorted(weekly[-8:],key=lambda r:r['ret_1w']),
                leaders=sorted(valid,key=lambda r:r['score'],reverse=True)[:15])
