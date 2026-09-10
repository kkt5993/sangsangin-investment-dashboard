"""Build public RS and momentum JSON from local prices, without network calls."""
import argparse
from datetime import datetime, timezone
import pandas as pd
from .analytics import PARAMETERS, align, clean, cumulative_excess, finite, relative_strength, trailing_return, ytd_return, zone
from .store import ROOT, load_prices, write_json
from .universe import PAIRS, ASSETS


def points(s):
    return [[str(d.date()), round(float(v),5)] for d,v in s.items() if finite(v) is not None]


def make_snapshots(prices, manifest, as_of):
    meta = dict(schema_version=1, as_of=as_of, generated_at=datetime.now(timezone.utc).isoformat(),
                source=manifest['provider'], vintage=manifest['vintage'], parameters=PARAMETERS,
                status='partial', method_note='팀 계산식으로 산출한 실데이터입니다. 비공개 원본 엔진과 수치 동등성은 미검증입니다.')
    rows, series, curves, quality = [], {}, {}, []
    for p in PAIRS:
        row = {**p, 'spread_pp':None, 'z':None, 'dz_1w':None, 'zone':'산출 불가', 'as_of':None, 'reason':p['unresolved']}
        rows.append(row)
        if p['unresolved']:
            continue
        missing = [s for s in [p['a'],p['b']] if s not in prices]
        if missing:
            row['reason'] = '가격 수집 누락: '+', '.join(missing)
            continue
        f = align(prices[p['a']],prices[p['b']],as_of)
        if f.empty:
            row['reason'] = '두 종목의 공통 거래일 없음'
            continue
        row['as_of'] = str(f.index[-1].date())
        if (pd.Timestamp(as_of)-f.index[-1]).days > PARAMETERS['max_staleness_calendar_days']:
            row['reason'] = '마지막 공통 가격이 기준일보다 7일 이상 오래됨'
            continue
        rs = relative_strength(f)
        last = rs.iloc[-1]
        row.update(spread_pp=finite(last.spread_pp), z=finite(last.z), dz_1w=finite(last.dz_1w),
                   zone=zone(finite(last.z)), common_observations=len(f),
                   first_common_date=str(f.index[0].date()))
        cutoff = pd.Timestamp(as_of)-pd.DateOffset(years=5)
        history = rs.z.loc[cutoff:]
        series[p['id']] = dict(points=points(history), start=str(cutoff.date()), end=as_of,
                               y_label='RS z-score (5Y)', y_domain=PARAMETERS['rs_y_domain'], guides=[-2,-1,0,1,2])
        if row['z'] is None:
            row['reason'] = '63일 수익률 + 1,260개 분포 관측치가 부족하거나 분산이 0'
        if p['sector']:
            curves[p['id']] = {}
            for months in [3,6]:
                s, base = cumulative_excess(f, months)
                curves[p['id']][str(months)] = dict(points=points(s), start=base, end=row['as_of'],
                                                  last=finite(s.iloc[-1]) if len(s) else None,
                                                  y_label='누적 초과수익률 (%)', guides=[0],
                                                  reason=None if len(s) else '기간 시작점 이전의 공통 가격 부족')
    for symbol, item in manifest['instruments'].items():
        quality.append({k:item.get(k) for k in ['status','rows','first_date','last_date','retrieved_at','currency','sha256']} | {'symbol':symbol})
    # Rank all 32 assets on one common date, including BTC versus US holidays.
    # Missing instruments remain missing and cannot hold the remaining set hostage.
    common_dates = None
    for a in ASSETS:
        if a['symbol'] in prices and len(prices[a['symbol']].dropna()):
            idx = clean(prices[a['symbol']],as_of).index
            if not len(idx) or (pd.Timestamp(as_of)-idx[-1]).days>PARAMETERS['max_staleness_calendar_days']:
                continue
            common_dates = idx if common_dates is None else common_dates.intersection(idx)
    asset_as_of = str(common_dates[-1].date()) if common_dates is not None and len(common_dates) else as_of
    asset_rows = []
    for a in ASSETS:
        row = {**a, 'returns':{k:None for k in ['1W','1M','3M','YTD','1Y']},
               'excess_3m_pp':None,'as_of':None,'reason':None}
        asset_rows.append(row)
        if a['symbol'] not in prices or 'SPY' not in prices:
            row['reason'] = '가격 수집 누락'
            continue
        # Common US market dates also align BTC to the ETF comparison calendar.
        f = align(prices[a['symbol']],prices['SPY'],asset_as_of)
        if f.empty or (pd.Timestamp(as_of)-f.index[-1]).days > 7:
            row['reason'] = '공통 가격 없음 또는 오래된 가격'
            continue
        row['as_of'] = str(f.index[-1].date())
        row['returns'] = {k:trailing_return(f.a,n) for k,n in PARAMETERS['return_sessions'].items() if k != '6M'}
        row['returns']['YTD'] = ytd_return(f.a)
        spy3 = trailing_return(f.b,63)
        row['excess_3m_pp'] = row['returns']['3M']-spy3 if spy3 is not None and row['returns']['3M'] is not None else None
    rs = dict(meta, module='rs', pairs=rows, series=series,
              stock_rankings={'status':'unavailable','reason':'원본의 KR·US 대형주 전체 유니버스와 KOSPI200 선별 규칙이 미공개입니다. 임의 종목 목록으로 순위를 만들지 않습니다.'},
              coverage={'pairs':sum(r['z'] is not None for r in rows),'expected_pairs':35,'expected_charts':35},
              quality=quality)
    sectors = [r for r in rows if r['sector']]
    # Same ranked sector identities receive both the 3M and 6M charts.
    ranked = sorted([r for r in sectors if r['z'] is not None],key=lambda r:r['z'],reverse=True)
    chosen = ranked if len(ranked)<=16 else ranked[:8]+ranked[-8:]
    mom = dict(meta, module='momentum', asset_as_of=asset_as_of, assets=asset_rows, sectors=sectors, curves=curves,
               chart_pairs=[r['id'] for r in chosen],
               coverage={'assets':sum(r['returns']['3M'] is not None for r in asset_rows), 'expected_assets':32,
                         'sectors':sum(r['z'] is not None for r in sectors),'expected_sectors':24,
                         'charts':len(chosen)*2,'expected_charts':32}, quality=quality)
    return rs,mom


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--vintage', required=True)
    p.add_argument('--as-of', help='Optional earlier calculation cutoff in this data vintage')
    args = p.parse_args()
    as_of = args.as_of or args.vintage
    if pd.Timestamp(as_of) > pd.Timestamp(args.vintage):
        p.error('Calculation date may not exceed data vintage')
    prices, manifest = load_prices(args.vintage,as_of)
    if not prices or not any(len(p) for p in prices.values()):
        p.error('No price data at the requested cutoff; keep the existing published snapshots.')
    rs,mom = make_snapshots(prices,manifest,as_of)
    out = ROOT/'docs/data'
    write_json(out/'rs.json',rs)
    write_json(out/'momentum.json',mom)
    print('RS',rs['coverage'])
    print('Momentum',mom['coverage'])
    print('Public derived JSON bytes:',sum((out/n).stat().st_size for n in ['rs.json','momentum.json']))


if __name__ == '__main__':
    main()
