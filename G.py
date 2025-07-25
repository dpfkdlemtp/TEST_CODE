import re
import pdfplumber

# -------------------------------
# ✅ 1) WPPSI 지표 점수 추출 (3페이지)
# -------------------------------
def extract_wppsi_scores_from_page3(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[2]
        text = page.extract_text()

    lines = text.split('\n')
    result = {}

    # ✅ 도메인 구분 (4세 이상 / 미만)
    if "4세이상" in pdf_path or "4세 이상" in pdf_path:
        domains = ["언어이해", "시공간", "유동추론", "작업기억", "처리속도", "전체IQ"]
    else:
        domains = ["언어이해", "시공간", "작업기억", "전체IQ"]

    domain_index = 0
    pattern = re.compile(
        r"(\d+)\s+(\d+)\s+([\d.]+)\s+(\d+)\s*-\s*(\d+)\s*\(\s*\d+\s*-\s*\d+\s*\)\s+([가-힣\s]{2,6})\s+([\d.]+)"
    )

    for line in lines:
        match = pattern.search(line)
        if match:
            domain = None
            for d in domains:
                if d in line:
                    domain = d
                    break
            if domain is None and domain_index < len(domains):
                domain = domains[domain_index]
                domain_index += 1

            result[domain] = {
                "환산점수합": match.group(1),
                "지표점수": match.group(2),
                "백분위": match.group(3),
                "신뢰구간": f"{match.group(4)}-{match.group(5)}",
                "진단분류": match.group(6).strip(),
                "SEM": match.group(7)
            }

    # ✅ 변수 자동 생성
    for domain, values in result.items():
        for k, v in values.items():
            var_name = f"{domain}_{k}".replace("%", "퍼센트").replace("~", "_").replace(" ", "_")
            globals()[var_name] = v

    return result

# -------------------------------
# ✅ 2) WPPSI 소검사 점수 추출 (2페이지)
# -------------------------------
def extract_wppsi_subtest_scores(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[1]  # ✅ WPPSI도 2페이지 인덱스 1
        text = page.extract_text()

    lines = text.split("\n")

    if "4세이상" in pdf_path or "4세 이상" in pdf_path:
        index = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        # ✅ WPPSI 4세 미만 소검사명 (K-WPPSI 매뉴얼 순서 기반)
        subtest_name_map = [
            ("시공간", "토막짜기"),
            ("언어이해", "상식"),
            ("유동추론", "행렬추리"),
            ("처리속도", "동형찾기"),
            ("작업기억", "그림기억"),
            ("언어이해", "공통성"),
            ("유동추론", "공통그림찾기"),
            ("처리속도", "선택하기"),
            ("작업기억", "위치찾기"),
            ("시공간", "모양맞추기"),
            ("언어이해", "어휘"),
        ]
    else:

        index = [2, 3, 4, 5, 6, 7, 8]
        # ✅ WPPSI 4세 미만 소검사명 (K-WPPSI 매뉴얼 순서 기반)
        subtest_name_map = [
            ("언어이해", "수용어휘"),
            ("시공간", "토막짜기"),
            ("작업기억", "그림기억"),
            ("언어이해", "상식"),
            ("시공간", "모양맞추기"),
            ("작업기억", "위치찾기"),
            ("언어이해", "그림명명"),
        ]

    # ✅ 숫자만 필터링 (환산점수만 추출)
    numbers = []
    for i, line in enumerate(lines):
        if i in index:
            j = 0
            for token in line.strip().split():
                if token.isdigit():
                    j += 1
                    if j == 2:
                        numbers.append(int(token))


    result = {}
    for i, (domain, name) in enumerate(subtest_name_map):
        value = numbers[i] if i < len(numbers) else None
        var_name = f"{domain}_{name}".replace(" ", "_")
        globals()[var_name] = value
        result[var_name] = value

    return result

# -------------------------------
# ✅ 실행 (통합)
# -------------------------------
if __name__ == "__main__":
    pdf_path = "K-WPPSI-IV(유아용)_4세이상.pdf"

    print("\n▶ WPPSI 지표 점수")
    scores_page3 = extract_wppsi_scores_from_page3(pdf_path)
    for domain, values in scores_page3.items():
        print(f"{domain}: {values}")

    print("\n▶ WPPSI 소검사 환산점수")
    subtest_scores = extract_wppsi_subtest_scores(pdf_path)
    for k, v in subtest_scores.items():
        print(f"{k} = {v}")
