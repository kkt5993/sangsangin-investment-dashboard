"""Install pinned, local-only OCR assets; never download user documents."""
import base64,gzip,hashlib,io,json,sys,tarfile
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pipeline.acquire import budget
from pipeline.store import DATA,write_json

PACKAGES=[
 ('tesseract.js','6.0.1','/sPvMvrCtgxnNRCjbTYbr7BRu0yfWDsMZQ2a/T5aN/L1t8wUQN6tTWv6p6FwzpoEBA0jrN2UD2SX4QQFRdoDbA==',{'dist/tesseract.min.js':'tesseract.min.js','dist/worker.min.js':'worker.min.js','LICENSE.md':'LICENSE','dist/tesseract.min.js.LICENSE.txt':'tesseract.min.js.LICENSE.txt','dist/worker.min.js.LICENSE.txt':'worker.min.js.LICENSE.txt'}),
 ('tesseract.js-core','6.0.0','1Qncm/9oKM7xgrQXZXNB+NRh19qiXGhxlrR8EwFbK5SaUbPZnS5OMtP/ghtqfd23hsr1ZvZbZjeuAGcMxd/ooA==',{'tesseract-core-lstm.wasm.js':'core/tesseract-core-lstm.wasm.js','tesseract-core-simd-lstm.wasm.js':'core/tesseract-core-simd-lstm.wasm.js','LICENSE':'core/LICENSE'})]

def download(url,path,limit):
    if path.exists():return path.read_bytes()
    budget(limit)
    with requests.get(url,stream=True,timeout=(10,45)) as r:
        r.raise_for_status();parts=[];size=0
        for chunk in r.iter_content(65536):
            size+=len(chunk)
            if size>limit:raise ValueError('OCR dependency download exceeds limit')
            parts.append(chunk)
    raw=b''.join(parts);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);return raw

def main():
    cache=DATA/'runtime/dependencies';dest=ROOT/'docs/vendor/ocr';manifest_path=ROOT/'config/ocr_vendor.json'
    previous=json.loads(manifest_path.read_text()) if manifest_path.exists() else {};selected={};sources=[]
    for name,version,integrity,names in PACKAGES:
        url=f'https://registry.npmjs.org/{name}/-/{name}-{version}.tgz'
        raw=download(url,cache/f'{name}-{version}.tgz',16*2**20)
        if base64.b64encode(hashlib.sha512(raw).digest()).decode()!=integrity:raise ValueError('OCR npm integrity mismatch')
        with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
            for source,target in names.items():selected[target]=archive.extractfile('package/'+source).read()
        sources.append(dict(url=url,integrity='sha512-'+integrity))
    for name in ['eng.traineddata','kor.traineddata','LICENSE']:
        model='best' if name=='kor.traineddata' else 'fast'
        url=f'https://raw.githubusercontent.com/tesseract-ocr/tessdata_{model}/4.1.0/'+name
        raw=download(url,cache/(f'tessdata-{model}-4.1.0-'+name),16*2**20)
        sha=hashlib.sha256(raw).hexdigest();prior=next((r for r in previous.get('sources',[]) if r['url']==url),None)
        if prior and prior['sha256']!=sha:raise ValueError('OCR language source changed')
        sources.append(dict(url=url,sha256=sha))
        selected['lang/'+name+('.gz' if name.endswith('.traineddata') else '')]=gzip.compress(raw,mtime=0) if name.endswith('.traineddata') else raw
    size=sum(map(len,selected.values()))
    if size>24*2**20:raise ValueError('OCR public assets exceed 24MiB')
    budget(size);files=[]
    for name,raw in sorted(selected.items()):
        path=dest/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        files.append(dict(path=path.relative_to(ROOT/'docs').as_posix(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    write_json(manifest_path,dict(name='tesseract.js',version='6.0.1',core='6.0.0',languages='tessdata_fast 4.1.0 eng / tessdata_best 4.1.0 kor',license='Apache-2.0',sources=sources,files=files))
    print(json.dumps(dict(public_files=len(files),public_bytes=size)))

if __name__=='__main__':main()
