import streamlit as st
import pandas as pd
import os

# === 기존 추출 함수 import ===
from G import extract_wppsi_scores_from_page3, extract_wppsi_subtest_scores
from F import extract_wisc_scores_from_page3, extract_wisc_subtest_scores
from E import extract_combination_scores_from_page4, extract_subtest_scores_from_page3, subtest_name_map

# -------------------------------
# ✅ PDF 종류 자동 감지
# -------------------------------
def extract_all_scores(pdf_path):
    filename = os.path.basename(pdf_path).upper()
    result = {"지표점수": {}, "소검사점수": {}}

    if "WPPSI" in filename:
        result["지표점수"] = extract_wppsi_scores_from_page3(pdf_path)
        result["소검사점수"] = extract_wppsi_subtest_scores(pdf_path)
    elif "WISC" in filename:
        result["지표점수"] = extract_wisc_scores_from_page3(pdf_path)
        result["소검사점수"] = extract_wisc_subtest_scores(pdf_path)
    elif "WAIS" in filename:
        result["지표점수"] = extract_combination_scores_from_page4(pdf_path)
        result["소검사점수"] = extract_subtest_scores_from_page3(pdf_path, subtest_name_map)

    return result, filename

# -------------------------------
# ✅ 지표 점수 변환 (WAIS 대응)
# -------------------------------
def format_index_scores_excel(scores, is_wais=False):
    if is_wais:
        ordered_keys = ["전체검사", "언어이해", "지각추론", "작업기억", "처리속도"]
        data = {"지표점수": [], "백분위": [], "진단분류": []}

        for key in ordered_keys:
            if key in scores:
                data["지표점수"].append(scores[key].get("조합점수", ""))
                data["백분위"].append(scores[key].get("백분위", ""))
                data["진단분류"].append("")  # WAIS에는 진단분류가 없음
            else:
                data["지표점수"].append("")
                data["백분위"].append("")
                data["진단분류"].append("")
    else:
        ordered_keys = ["전체IQ", "언어이해", "시공간", "유동추론", "작업기억", "처리속도"]
        data = {"지표점수": [], "백분위": [], "진단분류": []}

        for key in ordered_keys:
            if key in scores:
                data["지표점수"].append(scores[key].get("지표점수", ""))
                data["백분위"].append(scores[key].get("백분위", ""))
                data["진단분류"].append(scores[key].get("진단분류", ""))
            else:
                data["지표점수"].append("")
                data["백분위"].append("")
                data["진단분류"].append("")

    df = pd.DataFrame(data, index=ordered_keys).T
    return df

# -------------------------------
# ✅ 소검사 점수 변환
# -------------------------------
def format_subtest_scores_excel(scores):
    grouped = {}
    for k, v in scores.items():
        if "_" in k:
            domain, name = k.split("_", 1)
        else:
            domain, name = "기타", k
        grouped.setdefault(domain, {})[name] = v

    ordered_domains = ["언어이해", "시공간", "유동추론", "지각추론", "작업기억", "처리속도", "기타"]

    table_data = {}
    for domain in ordered_domains:
        if domain in grouped:
            for subtest, val in grouped[domain].items():
                table_data.setdefault(domain, []).append((subtest, val))

    columns = []
    values = []
    for domain, items in table_data.items():
        for subtest, _ in items:
            columns.append((domain, subtest))
        for subtest, val in items:
            values.append(val if val is not None else "")

    if not columns:
        return pd.DataFrame()
    df = pd.DataFrame([values], columns=pd.MultiIndex.from_tuples(columns))
    return df

# -------------------------------
# ✅ Streamlit UI
# -------------------------------
# --- 기존의 마지막 부분 ---
if __name__ == "__main__":
    st.title("📊 심리검사 점수 추출기")
    st.markdown("업로드한 **K-WPPSI / K-WISC / K-WAIS** PDF에서 점수를 자동으로 추출합니다.")

    uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])

    if uploaded_file is not None:
        save_path = f"./temp_{uploaded_file.name}"
        with open(save_path, "wb") as f:
            f.write(uploaded_file.read())

        st.success(f"✅ 업로드 완료: {uploaded_file.name}")

        with st.spinner("점수 추출 중..."):
            scores, filename = extract_all_scores(save_path)

        is_wais = "WAIS" in filename

        # ✅ 지표 점수 출력
        if scores["지표점수"]:
            st.subheader("📌 지표 점수")
            df_index = format_index_scores_excel(scores["지표점수"], is_wais=is_wais)
            st.dataframe(df_index.fillna(""), use_container_width=True)

            # ✅ 엑셀 다운로드
            excel_index = df_index.to_csv(index=True).encode("utf-8-sig")
            st.download_button("⬇️ 지표 점수 다운로드 (CSV)", excel_index, "index_scores.csv", "text/csv")

        # ✅ 소검사 점수 출력
        if scores["소검사점수"]:
            st.subheader("📌 소검사 점수")
            df_subtest = format_subtest_scores_excel(scores["소검사점수"])
            st.dataframe(df_subtest.fillna(""), use_container_width=True)

            # ✅ 엑셀 다운로드
            if not df_subtest.empty:
                excel_subtest = df_subtest.to_csv(index=False).encode("utf-8-sig")
                st.download_button("⬇️ 소검사 점수 다운로드 (CSV)", excel_subtest, "subtest_scores.csv", "text/csv")

        os.remove(save_path)
