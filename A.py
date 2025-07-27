import streamlit as st

# ---------------------------
# 기존 모듈 임포트
# ---------------------------
from D import (
    extract_pat_percentiles_from_bytes, explain_results
)

from C import (
    extract_tci_percentiles, extract_tci_m_sd, build_matching_Temperament_keys,
    build_matching_Summary_keys, find_best_matching_key, load_temperament_dict_from_drive
)
from B import (
    extract_all_scores, format_index_scores_excel, format_subtest_scores_excel
)
import os


# ---------------------------
# ✅ Streamlit UI
# ---------------------------
st.set_page_config(page_title="심리검사 통합 분석", layout="wide")
st.title("📊 심리검사 통합 분석 웹")

tabs = st.tabs(["🧠 지능검사", "📝 TCI", "📄 PAT"])

# ---------------------------
# 1️⃣ 지능검사 탭
# ---------------------------
with tabs[0]:
    st.header("🧠 지능검사 점수 추출기")
    uploaded_file = st.file_uploader("PDF 업로드 (K-WPPSI / K-WISC / K-WAIS)", type=["pdf"], key="지능검사")

    if uploaded_file:
        save_path = f"./temp_{uploaded_file.name}"
        with open(save_path, "wb") as f:
            f.write(uploaded_file.read())

        st.success(f"✅ 업로드 완료: {uploaded_file.name}")

        scores, filename = extract_all_scores(save_path)
        is_wais = "WAIS" in filename

        if scores["지표점수"]:
            st.subheader("📌 지표 점수")
            df_index = format_index_scores_excel(scores["지표점수"], is_wais=is_wais)
            st.dataframe(df_index.fillna(""), use_container_width=True)

        if scores["소검사점수"]:
            st.subheader("📌 소검사 점수")
            df_subtest = format_subtest_scores_excel(scores["소검사점수"])
            st.dataframe(df_subtest.fillna(""), use_container_width=True)

        os.remove(save_path)

# ---------------------------
# 2️⃣ TCI 탭
# ---------------------------
with tabs[1]:
    st.header("📝 TCI 결과 분석")
    tci_file = st.file_uploader("TCI PDF 업로드", type=["pdf"], key="TCI")

    if tci_file:
        with open("temp_tci.pdf", "wb") as f:
            f.write(tci_file.read())

        percentiles = extract_tci_percentiles("temp_tci.pdf")
        m_sd = extract_tci_m_sd("temp_tci.pdf")

        hml_values = {
            "자극추구": percentiles.get("자극추구", {}).get("level", "M"),
            "위험회피": percentiles.get("위험회피", {}).get("level", "M"),
            "사회적 민감성": percentiles.get("사회적 민감성", {}).get("level", "M"),
            "인내력": percentiles.get("인내력", {}).get("level", "M"),
            "자율성": percentiles.get("자율성", {}).get("level", "M"),
            "연대감": percentiles.get("연대감", {}).get("level", "M"),
        }

        st.subheader("✅ H/M/L 값")
        st.json(hml_values)

        data = load_temperament_dict_from_drive()
        matching_keys = build_matching_Temperament_keys(hml_values, m_sd)
        st.subheader("🔍 매칭 키")
        st.json(matching_keys)

        st.subheader("📌 최종 결과")
        for part, key in matching_keys.items():
            matched_key, status = find_best_matching_key(key, data.get(part, {}))
            st.markdown(f"### **[{part}]** - {status}")
            st.write(data.get(part, {}).get(matched_key, "❌ 설명 없음"))

        matching_keys = build_matching_Summary_keys(hml_values, m_sd)
        st.subheader("🔍 매칭 키")
        st.json(matching_keys)
        for part, key in matching_keys.items():
            matched_key, status = find_best_matching_key(key, data.get(part, {}))
            st.markdown(f"### **[{part}]** - {status}")
            st.write(data.get(part, {}).get(matched_key, "❌ 설명 없음"))

# ---------------------------
# 3️⃣ PAT 탭
# ---------------------------
with tabs[2]:
    st.header("📄 PAT PDF 분석기")
    pat_file = st.file_uploader("PAT PDF 업로드", type=["pdf"], key="PAT")

    if pat_file:
        data = extract_pat_percentiles_from_bytes(pat_file)
        st.subheader("✅ 분석 결과")
        st.write(f"**백분위:** {data['백분위']}")
        st.write(f"**결과:** {data['결과']}")

        if data["결과"]:
            ideal_titles, ideal_texts, non_titles, non_texts = explain_results(data["결과"])
            st.subheader(f"[이상적임] - {', '.join(ideal_titles)}")
            for txt in ideal_texts:
                st.write(txt)

            st.subheader(f"[미흡/지나침] - {', '.join(non_titles)}")
            for txt in non_texts:
                st.write(txt)

