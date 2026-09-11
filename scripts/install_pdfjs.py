"""Install the pinned, Apache-licensed browser PDF parser from official npm."""
import base64,hashlib,io,json,sys,tarfile
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pipeline.store import DATA,write_json

VERSION='6.3.289'
URL=f'https://registry.npmjs.org/pdfjs-dist/-/pdfjs-dist-{VERSION}.tgz'
INTEGRITY='ZHjSVpDa3D6izMq8/04lvkhkATUmL9px6ChPaXc1k6nU2Mrhlg1/7F0bdUqCwUjw3NsPTfPZsMDUU6ZIcRaeQw=='

def main():
    archive=DATA/'runtime/dependencies'/f'pdfjs-dist-{VERSION}.tgz'
    if archive.exists():raw=archive.read_bytes()
    else:
        with requests.get(URL,stream=True,timeout=(10,45)) as r:
            r.raise_for_status();parts=[]
            for chunk in r.iter_content(65536):
                parts.append(chunk)
        raw=b''.join(parts)
    if base64.b64encode(hashlib.sha512(raw).digest()).decode()!=INTEGRITY:raise ValueError('PDF.js npm integrity mismatch')
    selected={}
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tar:
        for member in tar.getmembers():
            name=member.name.removeprefix('package/')
            if name in ['legacy/build/pdf.min.mjs','legacy/build/pdf.worker.min.mjs','LICENSE'] or name.startswith(('cmaps/','standard_fonts/')):
                if not member.isfile():continue
                if '..' in Path(name).parts or Path(name).is_absolute():raise ValueError('Unexpected package path')
                selected[name]=tar.extractfile(member).read()
    archive.parent.mkdir(parents=True,exist_ok=True)
    if not archive.exists():archive.write_bytes(raw)
    out=ROOT/'docs/vendor/pdfjs';manifest=[]
    for name,data in sorted(selected.items()):
        path=out/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        manifest.append(dict(path=path.relative_to(ROOT/'docs').as_posix(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    write_json(ROOT/'config/pdfjs_vendor.json',dict(name='pdfjs-dist',version=VERSION,license='Apache-2.0',source=URL,integrity='sha512-'+INTEGRITY,files=manifest))
    print(json.dumps(dict(version=VERSION,archive_bytes=len(raw),public_files=len(manifest),public_bytes=sum(map(len,selected.values())))))

if __name__=='__main__':main()
