"""Synthetic finance pages with known text, scan copies and a mixed page."""
import io,json,os
from pathlib import Path
import pymupdf as fitz
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('SANGSANGIN_DATA_DIR',ROOT.parent/'sangsangin-investment-data'))/'runtime/pdf-ocr-fixtures'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    font=Path(os.environ.get('PDF_TEST_FONT',Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/malgun.ttf'))
    pdfmetrics.registerFont(TTFont('Korean',str(font)))
    english=['Investment research - test document','Revenue: 1,234.50 USD','Operating profit: -123.45 USD','Margin: -5.25% | Policy rate: 2.50%',
      'Period: 2026-09-08 | Scenario: A-17','Cash flow is different from accounting profit.',
      'Compare units, dates and source pages before making a decision.','This document contains synthetic data for extraction testing.',
      'A forecast is uncertain. The table values are not live market data.']
    korean=['상상인 투자 연구 - 검증용 문서','매출액 1,234.50억 원','영업이익 -123.45억 원','영업이익률 -5.25% | 정책금리 2.50%',
      '관측일 2026-09-08 | 분석 시나리오 A-17','현금흐름과 회계 이익은 서로 다른 지표입니다.',
      '투자 판단 전에 단위와 날짜 및 원문 페이지를 확인합니다.','이 문서에는 본문 추출 시험을 위한 합성 자료가 들어 있습니다.',
      '예측은 불확실하며 표에 기재한 값은 실제 시장 관측값이 아닙니다.']
    buf=io.BytesIO();c=canvas.Canvas(buf,pagesize=(595,842))
    for lines in [english,korean]:
        c.setFont('Korean',13)
        for i,line in enumerate(lines):c.drawString(40,775-i*35,line)
        c.showPage()
    c.save();source=fitz.open(stream=buf.getvalue(),filetype='pdf');out=fitz.open();out.insert_pdf(source)
    for i in range(2):
        page=out.new_page(width=595,height=842);page.insert_image(page.rect,stream=source[i].get_pixmap(dpi=200).tobytes('png'))
    page=out.new_page(width=595,height=842);page.insert_text((40,25),'Appendix - scanned table',fontsize=10)
    page.insert_image(fitz.Rect(0,35,595,842),stream=source[1].get_pixmap(dpi=200).tobytes('png'))
    out.new_page(width=595,height=842)
    out.save(OUT/'comparison.pdf',garbage=4,deflate=True)
    gold=['\n'.join(english),'\n'.join(korean),'\n'.join(english),'\n'.join(korean),'Appendix - scanned table\n'+'\n'.join(korean),'']
    (OUT/'expected.json').write_text(json.dumps(gold,ensure_ascii=False),encoding='utf8')
    for i in range(len(out)):out[i].get_pixmap(dpi=72).save(OUT/f'preview-{i+1}.png')
    print(json.dumps({'pages':len(out),'bytes':(OUT/'comparison.pdf').stat().st_size}))

if __name__=='__main__':main()
