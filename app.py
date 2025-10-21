import streamlit as st
import pdfplumber
import pandas as pd
from difflib import SequenceMatcher
from pdf2image import convert_from_path
import pytesseract
from io import BytesIO
import tempfile

# ------------------------------
# 기본 설정
# ------------------------------
st.set_page_config(page_title="단상자 아트웍 검증 툴", layout="wide")
st.title("📦 단상자 아트웍 자동 검증 툴 (AI / PDF 지원)")

st.markdown("""
이 툴은 **AI / PDF 단상자 아트웍 파일**을 자동으로 분석하여  
✅ **오타 검증**과 ✅ **기준 문구 비교 검증**을 수행합니다.  
---
""")

# 사이드바 언어 설정
st.sidebar.header("🌐 OCR 언어 설정")
lang_option = st.sidebar.selectbox(
    "OCR 인식 언어를 선택하세요",
    ["한글만 (kor)", "영어만 (eng)", "한글+영어 (kor+eng)"],
    index=2
)
lang_code = lang_option.split("(")[-1].replace(")", "").strip()

# 탭 설정
tab1, tab2 = st.tabs(["✏️ 오타 검증", "📊 기준 텍스트 비교"])

# ------------------------------
# TAB 1: 오타 검증 (엑셀 없음)
# ------------------------------
with tab1:
    st.subheader("✏️ 오타 검증 (엑셀 불필요)")
    uploaded_file = st.file_uploader("AI 또는 PDF 파일 업로드", type=["pdf", "ai"], key="file_1")

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            pdf_path = tmp_file.name

        # 텍스트 추출
        extracted_text = ""
        use_ocr = False

        with st.spinner("🔍 PDF/AI 파일에서 텍스트 추출 중..."):
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    pages_text = [p.extract_text() for p in pdf.pages if p.extract_text()]
                    extracted_text = "\n".join(pages_text)
            except Exception:
                extracted_text = ""

        # OCR fallback
        if len(extracted_text.strip()) < 50:
            use_ocr = True
            st.info(f"📸 텍스트 인식 불가 → OCR 모드 전환 ({lang_option})")
            images = convert_from_path(pdf_path, 300)
            text_blocks = [pytesseract.image_to_string(img, lang=lang_code) for img in images]
            extracted_text = "\n".join(text_blocks)

        # 기본 오타 감지 로직
        common_typos = {
            "Vitamn": "Vitamin",
            "miligram": "milligram",
            "mg.": "mg",
            "비타민C": "비타민 C",
            "mll": "mL"
        }
