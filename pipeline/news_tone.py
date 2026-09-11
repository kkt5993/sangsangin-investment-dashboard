"""Local, revision-pinned financial headline classification with exact-input reuse."""
import argparse,copy,hashlib,json,math,re,time,unicodedata,os,sys
from datetime import datetime,timezone
from pathlib import Path
from .store import ROOT,DATA,read_json
from .guru_data import read,save,resources
from .attention_data import age

FILE='company_news/tone.json.gz'
LABELS=('positive','negative','neutral')


def settings():return read_json(ROOT/'config/news_tone.json')
def text(value):return ' '.join(unicodedata.normalize('NFC',value or '').split())
def fingerprint(spec):
    fields={k:spec[k] for k in ['repo','revision','files','max_tokens','score']}
    return hashlib.sha256(json.dumps(fields,sort_keys=True).encode()).hexdigest()
def key(title,spec):return hashlib.sha256((fingerprint(spec)+'\n'+text(title)).encode()).hexdigest()
def checksum(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def verify_model(folder,spec):
    for name,expected in spec['files'].items():
        path=folder/name
        if not path.is_file() or checksum(path)!=expected:raise ValueError('Local model missing or changed: '+name)


def prepare_model(spec=None):
    """Explicit provisioning only; scheduled classification never downloads weights."""
    import requests
    spec=spec or settings();folder=DATA/'models/finbert'/spec['revision'];folder.mkdir(parents=True,exist_ok=True)
    for name,expected in spec['files'].items():
        path=folder/name
        if path.is_file() and checksum(path)==expected:continue
        with requests.get(f"https://huggingface.co/{spec['repo']}/resolve/{spec['revision']}/{name}",stream=True,timeout=(15,60)) as response:
            response.raise_for_status();tmp=path.with_suffix(path.suffix+'.partial')
            with tmp.open('wb') as f:
                for chunk in response.iter_content(1024*1024):f.write(chunk)
            if checksum(tmp)!=expected:raise ValueError('Downloaded model hash mismatch: '+name)
            tmp.replace(path)
    verify_model(folder,spec);return folder


class Classifier:
    def __init__(self,spec):
        deps=Path(os.environ.get('SANGSANGIN_TONE_DEPS',DATA.parent/'sangsangin-investment-tools/news-tone-dependencies'))
        if deps.is_dir():sys.path.insert(0,str(deps))
        import torch
        from transformers import AutoTokenizer,AutoModelForSequenceClassification
        folder=DATA/'models/finbert'/spec['revision'];verify_model(folder,spec)
        torch.set_num_threads(spec['threads']);self.torch=torch;self.spec=spec
        self.tokenizer=AutoTokenizer.from_pretrained(folder,local_files_only=True)
        self.model=AutoModelForSequenceClassification.from_pretrained(folder,local_files_only=True,weights_only=True,use_safetensors=False).eval()
        self.labels=[self.model.config.id2label[i].lower() for i in range(3)]
        if set(self.labels)!=set(LABELS):raise ValueError('Model label contract changed')
    def __call__(self,titles):
        output=[None]*len(titles);inputs=[];indices=[]
        for i,title in enumerate(titles):
            # Feed language is English; retain unsupported scripts as unknown.
            if not re.search('[A-Za-z]',title) or re.search('[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]',title):
                output[i]=dict(available=False,reason='영문 모델의 지원 범위 밖 제목');continue
            tokens=self.tokenizer.encode(title,add_special_tokens=True,truncation=False)
            if len(tokens)>self.spec['max_tokens']:
                output[i]=dict(available=False,reason='모델 입력 토큰 범위 초과 · 잘라서 분류하지 않음',tokens=len(tokens));continue
            inputs.append(tokens);indices.append(i)
        if inputs:
            batch=self.tokenizer.pad({'input_ids':inputs},padding=True,return_tensors='pt')
            with self.torch.inference_mode():scores=self.model(**batch).logits.softmax(dim=-1).cpu().tolist()
            for i,tokens,prob in zip(indices,inputs,scores):
                probs=dict(zip(self.labels,prob));output[i]=dict(available=True,probabilities=probs,label=max(probs,key=probs.get),score=probs['positive']-probs['negative'],tokens=len(tokens))
        return output


def valid(row):
    if not isinstance(row,dict) or not row.get('available'):return False
    p=row.get('probabilities',{})
    return set(p)==set(LABELS) and all(isinstance(v,(int,float)) and math.isfinite(v) and 0<=v<=1 for v in p.values()) and abs(sum(p.values())-1)<1e-5 and row.get('label')==max(p,key=p.get) and isinstance(row.get('score'),(int,float)) and abs(row['score']-(p['positive']-p['negative']))<1e-6


def collect(d,classifier_factory=Classifier,now=None,spec=None,retry=False):
    from .company_news import FILE as FEEDS
    now=now or datetime.now(timezone.utc);spec=spec or settings()
    if now.tzinfo is None:raise ValueError('Timezone required')
    source=d.resource(FEEDS);feeds=read(source) if source.exists() else {};path=d.resource(FILE);packet=read(path) if path.exists() else {'entries':{}}
    titles={key(a['title'],spec):text(a['title']) for r in feeds.get('feeds',{}).values() for a in r.get('items',[]) if text(a.get('title'))}
    from .topic_news import FILE as TOPICS,local_articles,settings as topic_settings,matched
    topic_path=d.resource(TOPICS);topics=read(topic_path) if topic_path.exists() else {}
    extra=[a for r in topics.get('feeds',{}).values() for a in r.get('items',[])]
    definitions=topic_settings()
    extra += [a for a in local_articles(d) if any(matched(a['title'],r) for r in definitions)]
    titles.update({key(a['title'],spec):text(a['title']) for a in extra if text(a.get('title'))})
    missing={k:v for k,v in titles.items() if not(valid(packet['entries'].get(k)) or packet['entries'].get(k,{}).get('available') is False)}
    report=dict(attempted_at=now.isoformat(),status='reused',classified=0,reused=len(titles)-len(missing),inputs=len(titles),model_fingerprint=fingerprint(spec))
    if not missing:return report
    previous=packet.get('collection',{})
    if not retry and previous.get('status')=='error' and previous.get('model_fingerprint')==fingerprint(spec) and 0<=age(previous.get('attempted_at'),now)<1:return dict(report,status='backoff')
    packet=copy.deepcopy(packet);start=time.perf_counter()
    try:
        model=classifier_factory(spec);items=list(missing.items())
        for offset in range(0,len(items),spec['batch_size']):
            part=items[offset:offset+spec['batch_size']];results=model([v for _,v in part])
            if len(results)!=len(part):raise ValueError('Classifier result count changed')
            for (k,title),row in zip(part,results):
                if row.get('available') is not False and not valid(row):raise ValueError('Invalid classifier probabilities')
                packet['entries'][k]=dict(row,input_sha256=hashlib.sha256(title.encode()).hexdigest(),analyzed_at=now.isoformat());report['classified']+=1
        report['status']='ok'
    except Exception as exc:report.update(status='error',error=type(exc).__name__)
    report['seconds']=time.perf_counter()-start;packet.update(collection=report,model=dict(repo=spec['repo'],revision=spec['revision'],fingerprint=fingerprint(spec),url=spec['model_url']))
    save(d.base/FILE,packet);return report


def annotate(rows,packet,spec,fresh):
    articles=copy.deepcopy(rows);unique={}
    for a in articles:
        identity=key(a['title'],spec);r=packet.get('entries',{}).get(identity)
        a['tone']=dict(copy.deepcopy(r),key=identity) if valid(r) else dict(available=False,reason=(r or {}).get('reason','해당 제목의 분류 결과 미확보'))
        unique[identity]=a['tone']
    good=[r for r in unique.values() if r['available']];count=len(good);total=len(unique)
    score=sum(r['score'] for r in good)/count if count else None
    summary=dict(available=bool(count),complete=bool(total) and count==total,classified=count,total=total,score=score,
        labels={label:sum(r['label']==label for r in good) for label in LABELS},model=spec['repo'],revision=spec['revision'],
        analyzed_at=max([r['analyzed_at'] for r in good],default=None),positive_hit=bool(fresh and total and count==total and score>0),
        model_url=spec['model_url'],collection_status=packet.get('collection',{}).get('status','missing'))
    return articles,summary


def verify_summary(r):
    spec=settings();t=r['tone_summary'];unique={}
    for a in r['items']:
        z=a['tone'];identity=key(a['title'],spec)
        if z['available']:
            assert valid(z) and z['key']==identity
            assert z['input_sha256']==hashlib.sha256(text(a['title']).encode()).hexdigest()
            assert 0<z['tokens']<=spec['max_tokens'] and z['analyzed_at']<=t['analyzed_at']
        else:assert z['reason']
        unique[identity]=z
    good=[z for z in unique.values() if z['available']]
    assert t['total']==len(unique) and t['classified']==len(good)
    assert t['complete']==bool(unique and len(good)==len(unique))
    assert t['labels']=={k:sum(z['label']==k for z in good) for k in LABELS}
    if good:
        expected=sum(z['score'] for z in good)/len(good)
        assert math.isclose(t['score'],expected,abs_tol=1e-6) and math.isclose(r['tone'],expected,abs_tol=1e-6)
        assert t['model']==spec['repo'] and t['revision']==spec['revision']
    else:assert r['tone'] is None and t['score'] is None
    assert t['positive_hit']==bool(r['available'] and t['complete'] and t['score']>0)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--as-of');p.add_argument('--prepare-model',action='store_true');p.add_argument('--retry',action='store_true');a=p.parse_args()
    if a.prepare_model:print(prepare_model())
    elif a.as_of:print(json.dumps(collect(resources(a.as_of),retry=a.retry)))
    else:p.error('--as-of or --prepare-model required')
