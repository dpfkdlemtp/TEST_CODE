import pdfplumber
import logging
logging.getLogger("pdfminer").setLevel(logging.ERROR)

def extract_combination_scores_from_page4(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[3]  # 4번째 페이지
        text = page.extract_text()

    lines = text.split('\n')
    result_dict = {}
    labels = ["환산점수합", "조합점수", "백분위", "95%신뢰구간"]
    domains = ["언어이해", "지각추론", "작업기억", "처리속도", "전체검사"]

    # 각 줄에서 숫자 5개 이상 있는 줄만 추출
    rows = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) == 6 and parts[0] in labels:
            rows.append(parts)

    if len(rows) < 4:
        print("❗ 조합점수 데이터가 충분히 탐지되지 않았습니다.")
        return {}

    # 표 구조 구성
    for col in range(1, 6):  # 각 열 = 도메인별 점수
        domain = domains[col - 1]
        result_dict[domain] = {}
        for row in rows:
            label = row[0]
            value = row[col]
            result_dict[domain][label] = value

    return result_dict

def extract_subtest_scores_from_page3(pdf_path, subtest_name_map):
    """
    ✅ 약어(SI, VC...)가 나오는 줄을 기준으로,
       바로 다음 줄에서 점수만 가져와 지정된 순서(subtest_name_map)에 매핑
    """
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[2]  # 3페이지
        text = page.extract_text()

    lines = text.split("\n")

    score_parts = []
    for i, line in enumerate(lines):
        if all(x in line for x in ["SI", "VC", "IN", "CO", "BD"]):
            if i + 1 < len(lines):
                score_parts = [s for s in lines[i + 1].strip().split() if s.isdigit()]
            break

    if not score_parts:
        print("❗ 소검사 점수가 탐지되지 않았습니다.")
        return {}

    result = {}
    for i, (domain, name) in enumerate(subtest_name_map):
        value = int(score_parts[i]) if i < len(score_parts) else None
        var_name = f"{domain}_{name}".replace(" ", "_")
        globals()[var_name] = value
        result[var_name] = value

    return result

# ✅ 추가: 코드 → 도메인/한글명칭 매핑
subtest_name_map = [
    ("언어이해", "공통성"),
    ("언어이해", "어휘"),
    ("언어이해", "상식"),
    ("지각추론", "토막짜기"),
    ("지각추론", "행렬추론"),
    ("지각추론", "퍼즐"),
    ("작업기억", "숫자"),
    ("작업기억", "산수"),
    ("처리속도", "동형찾기"),
    ("처리속도", "기호쓰기")
]
