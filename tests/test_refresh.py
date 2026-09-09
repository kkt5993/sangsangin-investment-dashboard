import json,tempfile,unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from pipeline.cache import make_patch,apply_patch_frame,chain
from pipeline.incremental import completed_date,valid_frame,universe_symbols
from pipeline.refresh import price_cutoff,publish,prune_staging
from pipeline.subview_modules import event_returns
from pipeline.vercel_deploy import package_site,verify

def prices(n=12):
    f=pd.DataFrame(index=pd.bdate_range('2026-08-03',periods=n))
    f['close']=100.+np.arange(n);f['open']=f.close-1;f['high']=f.close+2;f['low']=f.close-2
    f['adjusted_close']=f.close*.98;f['volume']=1000.;f['dividend']=0.;f['split']=0.;f.index.name='date'
    return f

class RefreshTests(unittest.TestCase):
    def test_vercel_package_contains_only_public_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);site=root/'docs';site.mkdir();(site/'index.html').write_text('<html>test</html>');(site/'data').mkdir();(site/'data/refresh.json').write_text('{}')
            (root/'private.json').write_text('not for publication')
            package_site(site,root/'package')
            static=root/'package/.vercel/output/static'
            self.assertEqual((static/'index.html').read_text(),'<html>test</html>')
            self.assertFalse((static/'private.json').exists())
            self.assertEqual(json.loads((root/'package/.vercel/output/config.json').read_text())['version'],3)
            (site/'.env').write_text('secret')
            with self.assertRaises(ValueError):package_site(site,root/'invalid')

    def test_vercel_verification_requires_matching_public_bytes(self):
        with patch('pipeline.vercel_deploy.requests.get') as get:
            get.return_value.status_code=200;get.return_value.content=b'previous snapshot'
            self.assertFalse(verify('https://example.vercel.app',b'current snapshot'))
            get.return_value.content=b'current snapshot'
            self.assertTrue(verify('https://example.vercel.app',b'current snapshot'))

    def test_classification_lookup_does_not_expand_collection_universe(self):
        members={'kr_largecap':{'members':[{'symbol':'005930.KS'}]},'kr_sectors':{'members':[{'symbol':'005930.KS'},{'symbol':'OUTSIDE.KS'}]}}
        self.assertEqual(universe_symbols(members),{'005930.KS'})

    def test_delta_reconstructs_and_does_not_repeat_unchanged_history(self):
        all_=prices();old=all_.iloc[:10];new=all_.iloc[6:]
        delta=make_patch(old,new)
        self.assertEqual(len(delta['dates']),2)
        pd.testing.assert_frame_equal(apply_patch_frame(old,delta),all_,check_freq=False)
        pd.testing.assert_frame_equal(old,all_.iloc[:10])

    def test_dividend_adjustment_rescales_old_prefix(self):
        old=prices(10);new=prices();new['adjusted_close']*=.995
        delta=make_patch(old,new.iloc[6:])
        self.assertEqual(len(delta['dates']),2)
        pd.testing.assert_frame_equal(apply_patch_frame(old,delta),new,check_freq=False)

    def test_nonuniform_revision_or_split_requires_complete_history(self):
        old=prices();new=old.iloc[6:].copy();new.iloc[1,new.columns.get_loc('close')]+=3
        self.assertIsNone(make_patch(old,new))
        new=old.copy();new[['open','high','low','close','adjusted_close']]/=2
        self.assertIsNone(make_patch(old,new))
        self.assertIsNone(make_patch(old[['close','adjusted_close']],old))

    def test_bad_cache_ancestry_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'expanded/20260909T010000Z';base.mkdir(parents=True)
            (base/'parent.json').write_text(json.dumps({'vintage':base.name}),encoding='utf8')
            with self.assertRaises(ValueError):chain(root,base.name)
            with self.assertRaises(ValueError):chain(root,'../../elsewhere')

    def test_exchange_closes_and_crypto_are_separate(self):
        morning=datetime.fromisoformat('2026-09-09T08:00:00+09:00')
        evening=datetime.fromisoformat('2026-09-09T18:00:00+09:00')
        self.assertEqual(price_cutoff(morning),'2026-09-08')
        self.assertEqual(price_cutoff(evening),'2026-09-09')
        self.assertEqual(completed_date('005930.KS','2026-09-09',morning),'2026-09-08')
        self.assertEqual(completed_date('005930.KS','2026-09-09',evening),'2026-09-09')
        for symbol in ['SPY','SAP.DE','VOD.L']:
            self.assertEqual(completed_date(symbol,'2026-09-09',evening),'2026-09-08')
        self.assertEqual(completed_date('BTC-USD','2026-09-09',morning),'2026-09-07')
        self.assertEqual(completed_date('BTC-USD','2026-09-09',evening),'2026-09-08')
        monday=datetime.fromisoformat('2026-09-14T08:00:00+09:00')
        self.assertEqual(completed_date('SPY','2026-09-13',monday),'2026-09-11')

    def test_pead_excludes_announcement_reaction_and_unmatured_horizon(self):
        p=prices(12).close;b=pd.Series(100.,index=p.index)
        before=event_returns(p,b,'2026-08-07T12:00:00Z')
        after=event_returns(p,b,'2026-08-07T20:00:00Z')
        self.assertEqual(before['first_session'],'2026-08-07')
        self.assertEqual(after['first_session'],'2026-08-10')
        self.assertAlmostEqual(after['d5'],(p.iloc[10]/p.iloc[5]-1)*100,places=5)
        self.assertIsNone(after['d20']);self.assertIsNone(after['excess20'])
        self.assertEqual(after['curve'][0]['y'],0)
        self.assertIsNone(event_returns(p,b,'2026-08-07'))
        self.assertIsNone(event_returns(p,b,'2026-09-01T12:00:00Z'))

    def test_invalid_prices_do_not_enter_delta(self):
        f=prices();f.loc[f.index[-1],'close']=np.inf
        with self.assertRaises(ValueError):valid_frame(f,'SPY')
        f=prices();f.loc[f.index[-1],'volume']=-1
        with self.assertRaises(ValueError):valid_frame(f,'SPY')

    def test_dirty_tree_stops_before_public_files_are_replaced(self):
        with patch('pipeline.refresh.subprocess.check_output',return_value=' M docs/app.js'),patch('pipeline.refresh.shutil.copy2') as copy:
            with self.assertRaises(RuntimeError):publish(Path('unbuilt'),{},Path('unused'))
            copy.assert_not_called()

    def test_pruning_touches_only_old_disposable_stages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'expanded/20260901';raw.mkdir(parents=True);(raw/'data').write_text('preserve')
            for n in ['20260901','20260902','20260903']:
                p=root/'runtime/staging'/n;p.mkdir(parents=True);(p/'generated').write_text('copy')
            with patch('pipeline.refresh.RUNTIME',root/'runtime'):prune_staging(2)
            self.assertEqual(len(list((root/'runtime/staging').iterdir())),2)
            self.assertEqual((raw/'data').read_text(),'preserve')

if __name__=='__main__':unittest.main()
