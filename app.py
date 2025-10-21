import streamlit as st
import pdfplumber
import pytesseract
from PIL import Image
from io import BytesIO
import fitz  # PyMuPDF
import re
from spellchecker import SpellChecker
from hanspell import spell_checker

st.set_page_config(page_title="AI/PDF 텍스트 오타 검증기", layout="wide")

st.title("📄 AI/PDF 단상자 오타 검증기 (한글+영문 혼합 지원)")
st.markdown("""
이 도구는 **AI 또는 PDF 원화 파일**의 텍스트를 자동으로 추출하고  
한글과 영어의 **철자/오타를 동시에 검증**합니다.  
Poppler 설치 없이 Streamlit Cloud에서도 OCR 기능이 동작합니다.
---
""")

# OCR 언어 설정
lang_option = st.sidebar.selectbox(
    "OCR 인식 언어",
    ["한글만 (kor)", "영어만 (eng)", "한글+영어 (kor+eng)"],
    index=2
)
lang_code = lang_option.split("(")[-1].replace(")", "").strip()

uploaded_file = st.file_uploader("📄 AI 또는 PDF 파일 업로드", type=["pdf", "ai"])

if uploaded_file:
    with st.spinner("🔍 텍스트 추출 중..."):
        # PDF 텍스트 추출 시도
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            pdf_path = tmp_file.name

        extracted_text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages_text = [p.extract_text() for p in pdf.pages if p.extract_text()]
                extracted_text = "\n".join(pages_text)
        except Exception:
            extracted_text = ""

        # OCR fallback
        if len(extracted_text.strip()) < 50:
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
    st.text_area("📜 추출된 텍스트", extracted_text[:3000], height=400)

    # ------------------------
    # 오타 검증 로직
    # ------------------------
    st.markdown("## ✏️ 오타 검증 결과")

    # 1️⃣ 영어 철자 검사
    spell_en = SpellChecker()
    english_words = re.findall(r"[A-Za-z]+", extracted_text)
    english_typos = spell_en.unknown(english_words)

    english_results = []
    for word in english_typos:
        suggestion = spell_en.correction(word)
        english_results.append({"단어": word, "제안": suggestion})

    # 2️⃣ 한글 맞춤법 검사
    korean_sentences = re.findall(r"[가-힣\s]+", extracted_text)
    korean_text = " ".join(korean_sentences)
    checked = spell_checker.check(korean_text)
    korean_typos = []
    if checked.errors > 0:
        for token, orig, cand, error in checked.words:
            if error:
                korean_typos.append({"단어": token, "제안": cand})

    # 결과 출력
    if english_results or korean_typos:
        st.error("⚠️ 오타 또는 철자 오류가 감지되었습니다.")
        if english_results:
            st.subheader("🅰️ 영어 오타")
            st.table(english_results)
        if korean_typos:
            st.subheader("🇰🇷 한글 오타")
            st.table(korean_typos)
    else:
        st.success("✅ 오타가 감지되지 않았습니다!")

else:
    st.info("👆 먼저 AI 또는 PDF 파일을 업로드해주세요.")
