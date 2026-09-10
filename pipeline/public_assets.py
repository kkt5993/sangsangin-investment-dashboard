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
    if sum(p.stat().st_size for p in files.values())>8*1024*1024:raise ValueError('PDF runtime size exceeded')
    for name,p in files.items():
        if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()) or p.suffix not in {'.mjs','.bcmap','.pfb','.ttf',''}:raise ValueError('Unexpected PDF runtime path')
        if p.stat().st_size!=entries[name]['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=entries[name]['sha256']:raise ValueError('PDF runtime integrity mismatch: '+name)
    return {p for p in files.values() if p.suffix in {'.bcmap','.pfb','.ttf'}}
