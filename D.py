import streamlit as st
import os
import fitz  # PyMuPDF
from PIL import Image, ImageEnhance, ImageFilter
import re
import json
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import io
from googleapiclient.http import MediaIoBaseDownload
import pytesseract

import platform
import pytesseract

# ✅ OS에 따라 Tesseract 경로 자동 설정
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"  # Streamlit Cloud/Linux 기본 경로


def load_google_service_account_key():
    return st.secrets["gcp"]

# ✅ Google Drive 연결 함수
@st.cache_resource(ttl=3000, show_spinner=False)
def get_drive_service():
    scope = ['https://www.googleapis.com/auth/drive']
    key_dict = load_google_service_account_key()
    creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
    return build('drive', 'v3', credentials=creds)

# ✅ Google Drive에서 판단별_설명.json 로드
@st.cache_data(ttl=3000, show_spinner=False)
def load_explain_data_from_drive():
    service = get_drive_service()

    # Google Drive 공유 URL에서 파일 ID 추출
    file_id = "1n17KiyaQ5cp_xFjgzFtmrE2Hvoqh5aXC"

    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return json.load(fh)

# ✅ 기존 로컬 파일 대신 Drive에서 로드
explain_data = load_explain_data_from_drive()

# Tesseract 경로 (환경에 맞게 수정)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 이상적 범위
ideal_ranges = {
    "지지표현": (65, 85),
    "합리적 설명": (65, 85),
    "성취압력": (50, 70),
    "간섭": (40, 60),
    "처벌": (30, 50),
    "감독": (30, 50),
    "과잉기대": (20, 40),
    "비일관성": (10, 30)
}
factors_order = list(ideal_ranges.keys())

def extract_pat_graph_by_render(pdf_bytes, page_num=2):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_num]
    pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
    # 그래프 잘라내기
    graph_bbox = (82, 130, 550, 470)
    crop_pix = page.get_pixmap(matrix=fitz.Matrix(3, 3), clip=graph_bbox)
    return crop_pix.tobytes("png")

def preprocess_image(image_path):
    img = Image.open(image_path).convert("L")
    img = img.filter(ImageFilter.MedianFilter())
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)
    img = img.point(lambda x: 0 if x < 140 else 255, '1')
    return img

def evaluate_results(percentiles):
    results = []
    for i, value in enumerate(percentiles):
        low, high = ideal_ranges[factors_order[i]]
        if value < low:
            results.append("미흡함")
        elif value > high:
            results.append("지나침")
        else:
            results.append("이상적임")
    return results

def ocr_pat_graph(image_path):
    img = preprocess_image(image_path)
    text = pytesseract.image_to_string(img, lang="kor+eng")
    seq_match = re.search(r"(\d+\s+){7}\d+", text)
    numbers = []
    if seq_match:
        numbers = [int(n) for n in re.findall(r"\d+", seq_match.group()) if 10 <= int(n) <= 100]
    evaluated = evaluate_results(numbers) if len(numbers) == 8 else []
    return {"백분위": numbers, "결과": evaluated}

# 판단별 설명 로드
explain_data = load_explain_data_from_drive()

def explain_results(evaluated):
    ideal_titles, ideal_texts, non_titles, non_texts = [], [], [], []
    for key, value in zip(factors_order, evaluated):
        if value == "이상적임":
            ideal_titles.append(key)
            ideal_texts.append(explain_data[key]["이상적임"])
        elif value == "미흡함":
            non_titles.append(key)
            non_texts.append(explain_data[key]["미흡함"])
        elif value == "지나침":
            non_titles.append(key)
            non_texts.append(explain_data[key]["지나침"])
    return ideal_titles, ideal_texts, non_titles, non_texts

# ---------------------------
# ✅ Streamlit Web UI
# ---------------------------
# --- 기존의 마지막 부분 ---
if __name__ == "__main__":
    st.title("📄 PAT PDF 분석기")

    uploaded_pdf = st.file_uploader("PAT PDF 파일 업로드", type=["pdf"])

    if uploaded_pdf:
        # 그래프 이미지 추출
        graph_img_bytes = extract_pat_graph_by_render(uploaded_pdf.read())
        graph_img_path = "temp_graph.png"
        with open(graph_img_path, "wb") as f:
            f.write(graph_img_bytes)

        st.image(graph_img_path, caption="추출된 그래프", use_column_width=True)

        # OCR + 결과
        data = ocr_pat_graph(graph_img_path)
        st.subheader("✅ OCR 결과")
        st.write(f"**백분위:** {data['백분위']}")
        st.write(f"**결과:** {data['결과']}")

        # 설명 출력
        if data["결과"]:
            ideal_titles, ideal_texts, non_titles, non_texts = explain_results(data["결과"])

            st.subheader(f"[이상적임] 영역 설명 - {', '.join(ideal_titles)}")
            for txt in ideal_texts:
                st.write(txt)

            st.subheader(f"[미흡함 또는 지나침] 영역 설명 - {', '.join(non_titles)}")
            for txt in non_texts:
                st.write(txt)
