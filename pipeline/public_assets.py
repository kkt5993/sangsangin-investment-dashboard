"""Verify the vendored PDF runtime and its non-text font/CMap assets."""
import hashlib,json
from pathlib import Path

def pdf_assets(site,manifest):
    site=Path(site);root=site/'vendor/pdfjs'
    if not root.exists():
        if (site/'pdf-text.js').exists():raise ValueError('Missing PDF runtime')
        return set()
    data=json.loads(Path(manifest).read_text(encoding='utf8'))
    if data['name']!='pdfjs-dist' or data['version']!='6.3.289' or data['license']!='Apache-2.0':raise ValueError('Unexpected PDF parser version/license')
    entries={r['path']:r for r in data['files']}
    files={p.relative_to(site).as_posix():p for p in root.rglob('*') if p.is_file()}
    if len(entries)!=len(data['files']) or set(entries)!=set(files):raise ValueError('Missing or unlisted PDF runtime file')
    for name,p in files.items():
        if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()) or p.suffix not in {'.mjs','.bcmap','.pfb','.ttf',''}:raise ValueError('Unexpected PDF runtime path')
        if p.stat().st_size!=entries[name]['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=entries[name]['sha256']:raise ValueError('PDF runtime integrity mismatch: '+name)
    return {p for p in files.values() if p.suffix in {'.bcmap','.pfb','.ttf'}}

def ocr_assets(site,manifest):
    site=Path(site);root=site/'vendor/ocr'
    if not root.exists():
        if (site/'pdf-ocr.js').exists():raise ValueError('Missing OCR runtime')
        return set()
    data=json.loads(Path(manifest).read_text(encoding='utf8'))
    if (data['name'],data['version'],data['core'],data['license'])!=('tesseract.js','6.0.1','6.0.0','Apache-2.0'):raise ValueError('Unexpected OCR version/license')
    expected={'LICENSE','tesseract.min.js','worker.min.js','tesseract.min.js.LICENSE.txt','worker.min.js.LICENSE.txt','core/LICENSE','core/tesseract-core-lstm.wasm.js','core/tesseract-core-simd-lstm.wasm.js','lang/LICENSE','lang/eng.traineddata.gz','lang/kor.traineddata.gz'}
    entries={r['path']:r for r in data['files']};files={p.relative_to(site).as_posix():p for p in root.rglob('*') if p.is_file()}
    if len(entries)!=len(data['files']) or set(entries)!=set(files) or {p.relative_to(root).as_posix() for p in files.values()}!=expected:raise ValueError('Missing or unlisted OCR runtime file')
    for name,p in files.items():
        if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):raise ValueError('Unexpected OCR runtime path')
        if p.stat().st_size!=entries[name]['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=entries[name]['sha256']:raise ValueError('OCR runtime integrity mismatch: '+name)
    return {p for p in files.values() if p.suffix=='.gz'}


def font_assets(site,manifest):
    """Permit only the pinned UI font and its redistribution license."""
    site=Path(site);root=site/'assets/fonts'
    if not root.exists():
        css=site/'experience.css'
        if css.is_file() and 'assets/fonts/' in css.read_text(encoding='utf8'):raise ValueError('Missing UI font')
        return set()
    data=json.loads(Path(manifest).read_text(encoding='utf8'))
    if (data['name'],data['license'])!=('Pretendard Variable','OFL-1.1'):raise ValueError('Unexpected UI font/license')
    expected={'assets/fonts/PretendardVariable.woff2','assets/fonts/OFL.txt'}
    entries={r['path']:r for r in data['files']};files={p.relative_to(site).as_posix():p for p in root.rglob('*') if p.is_file()}
    if len(entries)!=len(data['files']) or set(entries)!=expected or set(files)!=expected:raise ValueError('Missing or unlisted UI font asset')
    for name,p in files.items():
        if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):raise ValueError('Unexpected UI font path')
        if p.stat().st_size!=entries[name]['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=entries[name]['sha256']:raise ValueError('UI font integrity mismatch: '+name)
    return {p for p in files.values() if p.suffix=='.woff2'}
def globe_assets(site,config):
    """Only exact published package bytes may bypass generic text/image checks."""
    site=Path(site);out=set()
    for folder,name,version,license_name in [('cesium','cesium','1.145.0','Apache-2.0'),('satellite','satellite.js','7.1.0','MIT')]:
        root=site/'vendor'/folder
        if not root.exists():
            if (site/'sauron-views.js').exists():raise ValueError('Missing globe runtime')
            continue
        data=json.loads((Path(config)/(folder+'_vendor.json')).read_text(encoding='utf8'))
        if (data['name'],data['version'],data['license'])!=(name,version,license_name):raise ValueError('Unexpected globe vendor identity')
        entries={r['path']:r for r in data['files']};files={p.relative_to(site).as_posix():p for p in root.rglob('*') if p.is_file()}
        if len(entries)!=len(data['files']) or set(entries)!=set(files):raise ValueError('Missing or unlisted globe runtime')
        for name,p in files.items():
            if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):raise ValueError('Unsafe globe asset path')
            if p.stat().st_size!=entries[name]['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=entries[name]['sha256']:raise ValueError('Globe runtime integrity mismatch: '+name)
        out.update(files.values())
    return out
