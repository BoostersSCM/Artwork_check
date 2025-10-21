import streamlit as st
import pdfplumber
import pytesseract
from PIL import Image
from io import BytesIO
import fitz  # PyMuPDF
import re
from spellchecker import SpellChecker

st.set_page_config(page_title="AI/PDF 오타 검증기", layout="wide")

st.title("📄 AI/PDF 단상자 오타 검증기 (한글+영문 혼합, Cloud 호환)")
st.markdown("""
이 도구는 **AI 또는 PDF 원화 파일**의 텍스트를 자동으로 추출하고  
**한글과 영어의 철자 오류를 동시에 탐지**합니다.  
Poppler가 없어도 Streamlit Cloud에서 정상 작동합니다.
---
""")

# OCR 언어 선택
lang_option = st.sidebar.selectbox(
    "OCR 인식 언어",
    ["한글만 (kor)", "영어만 (eng)", "한글+영어 (kor+eng)"],
    index=2
)
lang_code = lang_option.split("(")[-1].replace(")", "").strip()

uploaded_file = st.file_uploader("📄 AI 또는 PDF 파일 업로드", type=["pdf", "ai"])

# 한글 간단 오타 패턴 (기초 규칙 기반)
korean_common_typos = {
    "위하사": "위하여",
    "섭치": "섭취",
    "및줄": "및 줄",
    "합니다니다": "합니다",
    "잇습니다": "있습니다",
    "ㅂ니다": "습니다"
}

if uploaded_file:
    with st.spinner("🔍 텍스트 추출 중..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            pdf_path = tmp_file.name

        extracted_text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_blocks = [p.extract_text() for p in pdf.pages if p.extract_text()]
                extracted_text = "\n".join(text_blocks)
        except Exception:
            extracted_text = ""

        if len(extracted_text.strip()) < 50:
            st.info(f"📸 텍스트 인식 불가 → OCR 모드 전환 ({lang_option})")
            doc = fitz.open(pdf_path)
            ocr_texts = []
            for page in doc:
                pix = page.get_pixmap(dpi=300)
                img = Image.open(BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img, lang=lang_code)
                ocr_texts.append(text)
            extracted_text = "\n".join(ocr_texts)

    st.success("✅ 텍스트 추출 완료!")
    st.text_area("📜 추출된 텍스트", extracted_text[:3000], height=400)

    # 영어 오타 검사
    spell_en = SpellChecker()
    english_words = re.findall(r"[A-Za-z]+", extracted_text)
    english_typos = spell_en.unknown(english_words)

    english_results = [
        {"언어": "영문", "단어": word, "추천 수정": spell_en.correction(word)}
        for word in english_typos
    ]

    # 한글 오타 검사 (기초 규칙 기반)
    korean_typos = []
    for wrong, correct in korean_common_typos.items():
        if wrong in extracted_text:
            korean_typos.append({"언어": "한글", "단어": wrong, "추천 수정": correct})

    # 결과 출력
    all_typos = english_results + korean_typos
    if all_typos:
        st.error("⚠️ 오타 또는 철자 오류가 감지되었습니다.")
        st.dataframe(all_typos, use_container_width=True)
    else:
        st.success("✅ 오타가 감지되지 않았습니다!")
else:
    st.info("👆 먼저 AI 또는 PDF 파일을 업로드해주세요.")
