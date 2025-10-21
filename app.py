import streamlit as st
import pdfplumber
import pandas as pd
from difflib import SequenceMatcher
import pytesseract
from PIL import Image
from io import BytesIO
import tempfile
import fitz  # PyMuPDF

st.set_page_config(page_title="AI/PDF 아트웍 검증 툴", layout="wide")
st.title("📦 단상자 아트웍 자동 검증 툴 (Streamlit Cloud 호환)")

st.markdown("""
이 툴은 **AI / PDF 단상자 아트웍 파일**을 자동으로 분석합니다.  
Poppler가 없는 환경(Streamlit Cloud)에서도 **OCR 기능이 정상 작동**하도록 개선되었습니다.
---
""")

# 언어 설정
lang_option = st.sidebar.selectbox(
    "OCR 인식 언어 선택",
    ["한글만 (kor)", "영어만 (eng)", "한글+영어 (kor+eng)"],
    index=2
)
lang_code = lang_option.split("(")[-1].replace(")", "").strip()

uploaded_file = st.file_uploader("📄 AI 또는 PDF 파일 업로드", type=["pdf", "ai"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        pdf_path = tmp_file.name

    extracted_text = ""
    use_ocr = False

    # 1️⃣ 기본 텍스트 추출 시도
    with st.spinner("🔍 텍스트 추출 시도 중..."):
        try:
            with pdfplumber.open(pdf_path) as pdf:
                extracted_pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
                extracted_text = "\n".join(extracted_pages)
        except Exception:
            extracted_text = ""

    # 2️⃣ OCR fallback (PyMuPDF 사용)
    if len(extracted_text.strip()) < 50:
        use_ocr = True
        st.info(f"📸 텍스트 인식 불가 → OCR 모드 전환 ({lang_option})")

        doc = fitz.open(pdf_path)
        text_blocks = []
        for page in doc:
            pix = page.get_pixmap(dpi=300)
            img = Image.open(BytesIO(pix.tobytes("png")))
            ocr_text = pytesseract.image_to_string(img, lang=lang_code)
            text_blocks.append(ocr_text)
        extracted_text = "\n".join(text_blocks)

    st.success("✅ 텍스트 추출 완료!")
    if use_ocr:
        st.warning(f"⚠️ OCR 모드로 인식됨 ({lang_option})")

    st.text_area("📜 추출된 텍스트", extracted_text[:3000], height=400)
    st.download_button(
        "📥 전체 텍스트 다운로드",
        extracted_text.encode("utf-8"),
        "extracted_text.txt",
        "text/plain"
    )
