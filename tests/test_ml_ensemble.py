import unittest
import numpy as np
import pandas as pd
from pipeline.ml_ensemble import model_set,shadow_selection,select_model,calibration,walk_forward,explanation
from pipeline.ml_features import build_features,FORCED_KR


class MLFamilyTests(unittest.TestCase):
    def test_forced_features_and_future_horizon_maturity(self):
        rng=np.random.default_rng(5);dates=pd.date_range('2015-01-31',periods=66,freq='ME')
        X=pd.DataFrame(rng.normal(size=(66,4)),columns=['a','b','c','forced'],index=dates)
        X['absent']=np.nan;X['constant']=1
        p=pd.Series(100*np.exp(np.cumsum(rng.normal(0,.03,66))),index=dates)
        a=walk_forward(X.iloc[:58],p,3,forced=['forced','absent','constant'],min_train=48,shadow_repeats=2,lstm_epochs=2)
        change_X=X.copy();change_X.iloc[57:,:4]*=1000;change_p=p.copy();change_p.iloc[57:]*=2
        b=walk_forward(change_X.iloc[:58],change_p,3,forced=['forced','absent','constant'],min_train=48,shadow_repeats=2,lstm_epochs=2)
        self.assertIn('forced',a['selections'][0]['forced'])
        self.assertEqual(a['selections'][0]['unavailable_forced'],['absent','constant'])
        for key in ['prediction','models','selected_model','probability','interval']:
            self.assertEqual(a['records'][0][key],b['records'][0][key],key)
        for r in a['records']:
            self.assertLessEqual(r['train_target_end'],r['origin']);self.assertLess(r['origin'],r['target'])
        self.assertEqual(len(a['records'][0]['models']),12)

    def test_model_choice_and_residuals_wait_for_target_date(self):
        records=[dict(target='2020-03-31',actual=2.,models={'A':1.,'B':-1.}),dict(target='2020-05-31',actual=-100.,models={'A':100.,'B':-100.})]
        self.assertEqual(select_model(records,'2020-04-30',['A','B'],1),('A',1))
        p,interval,count=calibration(records,'2020-04-30','A',1.,1)
        self.assertEqual(count,1);self.assertEqual(interval['0.5'] if '0.5' in interval else interval['0.16'],2)

    def test_treeshap_is_additive_and_separate_from_oos(self):
        rng=np.random.default_rng(3);dates=pd.date_range('2010-01-31',periods=100,freq='ME')
        X=pd.DataFrame(rng.normal(size=(100,4)),columns=list('abcd'),index=dates);p=pd.Series(100*np.exp(np.cumsum(X.a)*.02),index=dates)
        result=explanation(X,p,1,{'selected':list(X.columns)})
        self.assertLess(result['additive_error'],1e-6);self.assertIn('not OOS',result['scope']);self.assertEqual(result['training_observations'],99)
        self.assertTrue(all(0<=point[1]<=1 for row in result['rows'] for point in row['points']))

    def test_transformer_replays_only_matured_history(self):
        from pipeline.ml_transformer import augment
        rng=np.random.default_rng(19);dates=pd.date_range('2015-01-31',periods=60,freq='ME')
        X=pd.DataFrame(rng.normal(size=(60,3)),columns=list('abc'),index=dates)
        p=pd.Series(100*np.exp(np.cumsum(rng.normal(0,.03,60))),index=dates)
        base=walk_forward(X,p,3,min_train=48,shadow_repeats=1,lstm_epochs=2)
        base.update(horizon=3,signature='fixture',parameters={})
        result=augment(base,X,p,epochs=2)
        changed=X.copy();changed.iloc[-1]*=1000
        other=augment(base,changed,p,epochs=2)
        self.assertEqual(result['records'][:-1],other['records'][:-1])
        for r in result['records']:
            self.assertEqual(len(r['models']),13)
            self.assertLessEqual(r['train_target_end'],r['origin'])
            self.assertLessEqual(r['transformer_fit_origin'],r['origin'])
            values=[v for k,v in r['models'].items() if not k.startswith('Ens-')]
            self.assertAlmostEqual(r['models']['Ens-Mean'],np.mean(values),places=4)
            self.assertAlmostEqual(r['models']['Ens-Median'],np.median(values),places=4)
        self.assertEqual(result['records'][0]['selected_model'],'Ens-Mean')
        self.assertEqual(result['records'][0]['calibration_observations'],0)


class MLFeatureTests(unittest.TestCase):
    def test_prefix_invariance_and_macro_month_lag(self):
        dates=pd.bdate_range('2004-01-01','2026-08-31');months=pd.date_range('2004-01-01','2026-08-01',freq='MS')
        class Data:
            def __init__(self,future=False):self.future=future
            def price(self,key):
                x=np.arange(len(dates));s=pd.Series(100*np.exp(.0001*x+.02*np.sin(x/40)),index=dates)
                if self.future:s.loc['2024-01-01':]*=np.linspace(1,3,len(s.loc['2024-01-01':]))
                return s
            def monthly(self,key):return self.price(key).resample('ME').last()
            def mac(self,key):
                s=pd.Series(100+np.arange(len(months))*.2,index=months)
                if self.future:s.loc['2024-01-01':]*=3
                return s
        a,_=build_features(Data(),'^GSPC');b,_=build_features(Data(True),'^GSPC')
        pd.testing.assert_frame_equal(a.loc[:'2023-12-31'],b.loc[:'2023-12-31'])
        self.assertTrue(set(FORCED_KR)<=set(a))
        self.assertEqual(a.loc['2023-12-31','OECD_CLI_KOR'],(19*12+9)*.2)


if __name__=='__main__':unittest.main()
