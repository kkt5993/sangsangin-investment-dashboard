import copy,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
from types import SimpleNamespace
from unittest.mock import patch
from pipeline import clinical_data as C
from pipeline.clinical_views import views

NOW=datetime(2026,9,11,tzinfo=timezone.utc)
SCOPE={'id':'x','name':'Example','entity':'stock:X','term':'AREA[LeadSponsorName]Example','definition':'sponsor'}
def response(count=1,status='RECRUITING',phase='PHASE3'):
 return dict(totalCount=count,studies=[dict(protocolSection=dict(identificationModule=dict(nctId='NCT00000001',briefTitle='Study'),statusModule=dict(overallStatus=status,lastUpdatePostDateStruct={'date':'2026-09-09'}),sponsorCollaboratorsModule={'leadSponsor':{'name':'Example'}},designModule={'phases':[phase]}))] if count else [])
class Session:
 def __init__(self,change=False,fail=False):self.calls=[];self.change=change;self.fail=fail
 def get(self,url,params,**kwargs):
  self.calls.append((url,params))
  if self.fail:raise RuntimeError('fixture network')
  value={'apiVersion':'2','dataTimestamp':'2026-09-10T09:00:04'} if url.endswith('version') else response()
  if self.change and len(self.calls)==5:value['dataTimestamp']='2026-09-11T09:00:04'
  return SimpleNamespace(raise_for_status=lambda:None,json=lambda:value)
class ClinicalTests(unittest.TestCase):
 def test_zero_and_status_phase_sort_identity_validation(self):
  self.assertEqual(C.normalize(response(0),'recruiting','2026-09-10')['count'],0)
  with self.assertRaises(ValueError):C.normalize(response(status='COMPLETED'),'recruiting','2026-09-10')
  with self.assertRaises(ValueError):C.normalize(response(phase='PHASE2'),'phase3','2026-09-10')
  with self.assertRaises(ValueError):C.normalize(response(),'all','2026-09-08')
  with self.assertRaises(ValueError):C.normalize({'totalCount':8,'studies':[]},'all','2026-09-10')
 def test_collection_cache_changed_registry_atomicity_and_retry(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(C,'settings',return_value={'version':1,'scopes':[SCOPE]}):
   root=Path(tmp);d=SimpleNamespace(base=root,resource=lambda p:root/p);s=Session();r=C.collect(d,s,NOW,lambda _:None);self.assertEqual(r['requests'],5);old=C.read(root/C.FILE);self.assertEqual(len(old['responses']),3);self.assertIsNone(old['scopes'][0]['changes']['all'])
   self.assertEqual(C.collect(d,Session(fail=True),NOW+timedelta(hours=1),lambda _:None)['requests'],0)
   same=Session();self.assertEqual(C.collect(d,same,NOW+timedelta(hours=25),lambda _:None)['requests'],1)
   self.assertEqual(C.read(root/C.FILE)['retrieved_at'],old['retrieved_at'])
   failure=Session(fail=True);result=C.collect(d,failure,NOW+timedelta(hours=50),lambda _:None);self.assertEqual(result['status'],'error');saved=C.read(root/C.FILE);self.assertEqual(saved['scopes'],old['scopes']);self.assertEqual(saved['retrieved_at'],old['retrieved_at'])
   self.assertEqual(C.collect(d,Session(fail=True),NOW+timedelta(hours=50,minutes=1),lambda _:None)['requests'],0)
   saved['data_version']='2026-09-09T09:00:04';C.save(root/C.FILE,saved)
   changed=Session(change=True);result=C.collect(d,changed,NOW+timedelta(hours=52),lambda _:None);self.assertEqual(result['status'],'error');self.assertEqual(C.read(root/C.FILE)['scopes'],old['scopes'])
 def test_query_change_does_not_inherit_counts_and_backoff(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(C,'settings',return_value={'version':1,'scopes':[SCOPE]}) as settings:
   root=Path(tmp);d=SimpleNamespace(base=root,resource=lambda p:root/p);C.collect(d,Session(),NOW,lambda _:None)
   settings.return_value={'version':2,'scopes':[{**SCOPE,'term':'Changed'}]}
   C.collect(d,Session(fail=True),NOW+timedelta(minutes=1),lambda _:None)
   self.assertEqual(C.collect(d,Session(),NOW+timedelta(minutes=2),lambda _:None)['requests'],0)
   C.collect(d,Session(),NOW+timedelta(hours=2),lambda _:None);packet=C.read(root/C.FILE);self.assertIsNone(packet['scopes'][0]['changes']['all']);self.assertEqual(packet['scopes'][0]['term'],'Changed')
 def test_views_keep_zero_scope_and_do_not_add_score(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(C,'settings',return_value={'version':1,'scopes':[SCOPE]}):
   root=Path(tmp);d=SimpleNamespace(base=root,resource=lambda p:root/p);C.collect(d,Session(),NOW,lambda _:None)
   obj={'missing':[],'sections':[{'type':'dragontriggers','items':[{'observed_score':4}],'log':[]}]};views(d,obj);first=copy.deepcopy(obj);views(d,obj);self.assertEqual(first,obj);self.assertEqual(obj['sections'][0]['items'][0]['observed_score'],4);self.assertEqual(obj['sections'][0]['log'][0]['kind'],'임상 등록부')
   p=C.read(root/C.FILE);p['scopes'][0]['groups']['recruiting']={'count':0,'latest':[]};C.save(root/C.FILE,p);views(d,obj);self.assertEqual(obj['sections'][0]['log'],[]);self.assertEqual(obj['sections'][-1]['items'][0]['groups']['recruiting']['count'],0)
if __name__=='__main__':unittest.main()
