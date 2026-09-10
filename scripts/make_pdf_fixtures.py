"""Generate small, synthetic PDF fixtures outside the public repository."""
import json,os,sys
from pathlib import Path
import pymupdf as fitz

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('SANGSANGIN_DATA_DIR',ROOT.parent/'sangsangin-investment-data'))/'runtime/pdf-fixtures'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    doc=fitz.open();p=doc.new_page();p.insert_text((50,70),'Research fixture - 2026-09-08',fontsize=16)
    p.insert_text((50,105),'Revenue 1,234.50 USD | Change -5.25% | Not a forecast',fontsize=11)
    p.insert_text((50,140),'First paragraph. Source text, not an AI summary.',fontsize=11)
    scan=p.get_pixmap(matrix=fitz.Matrix(1,1)).tobytes('png')
    p=doc.new_page();p.insert_text((50,70),'한국 금리 연구',fontname='korea',fontsize=18)
    p.insert_text((50,110),'정책금리 2.50% · 영업이익 -123억 원',fontname='korea',fontsize=13)
    p.insert_text((50,150),'원문과 근거를 보존합니다.',fontname='korea',fontsize=13)
    p=doc.new_page();p.insert_image(p.rect,stream=scan)
    doc.set_metadata({'title':'한국 금리 연구','author':'상상인 테스트'})
    doc.set_page_labels([{'startpage':0,'style':'r','firstpagenum':1}])
    doc.save(OUT/'mixed.pdf',garbage=4,deflate=True)
    doc.save(OUT/'encrypted.pdf',encryption=fitz.PDF_ENCRYPT_AES_256,user_pw='fixture-only',owner_pw='fixture-owner')
    for i in range(3):doc[i].get_pixmap(matrix=fitz.Matrix(1,1)).save(OUT/f'page-{i+1}.png')
    doc.close();long=fitz.open()
    for i in range(302):long.new_page().insert_text((50,70),f'Physical page {i+1}')
    long.save(OUT/'long.pdf',garbage=4,deflate=True);long.close()
    (OUT/'invalid.pdf').write_bytes(b'%PDF-1.7\nnot a valid document\n%%EOF')
    print(json.dumps({'directory':str(OUT),'pdfs':4,'preview_pages':3},ensure_ascii=True))

if __name__=='__main__':main()
