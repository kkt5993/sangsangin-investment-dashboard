import io, unittest
import pandas as pd
from pipeline.oecd_data import parse, AREAS


def fixture():
    return pd.DataFrame([dict(REF_AREA=a,FREQ='M',MEASURE='LI',UNIT_MEASURE='IX',ADJUSTMENT='AA',METHODOLOGY='H',UNIT_MULT='0',TIME_PERIOD=t.strftime('%Y-%m'),OBS_VALUE=100+i*.01) for a in AREAS for i,t in enumerate(pd.date_range('2020-01-01','2026-09-01',freq='MS'))])


class OECDTests(unittest.TestCase):
    def test_unordered_months_current_month_excluded(self):
        f=fixture().sample(frac=1,random_state=17);out=parse(f.to_csv(index=False).encode(),'2026-09-08')
        self.assertEqual(set(out),{'OECD_CLI_'+a for a in AREAS})
        for key,g in out.items():
            self.assertEqual(g.observation_date.iloc[-1],'2026-08-01')
            self.assertEqual(g[key].iloc[0],100)
            self.assertEqual(len(g),80)

    def test_dimensions_duplicates_gaps_and_stale_rejected(self):
        base=fixture()
        variants=[]
        for k in ['UNIT_MEASURE','ADJUSTMENT','UNIT_MULT','METHODOLOGY']:
            f=base.copy();f.loc[0,k]='wrong';variants.append(f)
        variants += [pd.concat([base,base.iloc[[0]]]),base.drop(index=5),base[base.TIME_PERIOD<'2026-01'],base[base.REF_AREA!='KOR']]
        for f in variants:
            with self.assertRaises(ValueError):parse(f.to_csv(index=False).encode(),'2026-09-08')


if __name__=='__main__':unittest.main()
