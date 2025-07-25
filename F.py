import pdfplumber

# -------------------------------
# ✅ 1) WISC 지표 점수 추출 (3페이지)
# -------------------------------
def extract_wisc_scores_from_page3(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[2]  # 3페이지 (0-based)
        text = page.extract_text()

    lines = text.split("\n")
    result = {}

    domains = ["언어이해", "시공간", "유동추론", "작업기억", "처리속도", "전체IQ"]
    domain_index = 0

    for line in lines:
        parts = line.strip().split()

        if (
            len(parts) >= 6
            and parts[0].isdigit()
            and parts[1].isdigit()
            and '-' in parts[3]
            and domain_index < len(domains)
        ):
            if len(parts) == 7:
                진단분류 = parts[4] + " " + parts[5]
                SEM = parts[6]
            else:
                진단분류 = parts[4]
                SEM = parts[5]

            result[domains[domain_index]] = {
                "환산점수합": parts[0],
                "지표점수": parts[1],
                "백분위": parts[2],
                "신뢰구간": parts[3],
                "진단분류": 진단분류,
                "SEM": SEM
            }
            domain_index += 1

    # ✅ 변수 자동 생성
    for domain, values in result.items():
        for k, v in values.items():
            var_name = f"{domain}_{k}".replace("%", "퍼센트").replace("~", "_").replace(" ", "_")
            globals()[var_name] = v

    return result

# -------------------------------
# ✅ 2) WISC 소검사 점수 추출 (2페이지)
# -------------------------------
def extract_wisc_subtest_scores(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[1]  # ✅ 2페이지
        text = page.extract_text()

    lines = text.split("\n")
    numbers = []

    for i, line in enumerate(lines):
        if i in [1, 2, 5, 6, 7, 8, 11, 12, 14, 15]:
            j = 0
            for token in line.strip().split():
                if token.isdigit():
                    j += 1
                    if j == 2:
                        numbers.append(int(token))

    subtest_name_map = [
        ("언어이해", "공통성"),
        ("언어이해", "어휘"),
        ("시공간", "토막짜기"),
        ("시공간", "퍼즐"),
        ("유동추론", "행렬추리"),
        ("유동추론", "무게비교"),
        ("작업기억", "숫자"),
        ("작업기억", "그림기억"),
        ("처리속도", "기호쓰기"),
        ("처리속도", "동형찾기"),
    ]

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
    pdf_path = "K-WISC-V(아동용).pdf"

    print("\n▶ WISC-V 지표 점수")
    scores_page3 = extract_wisc_scores_from_page3(pdf_path)
    for domain, values in scores_page3.items():
        print(f"{domain}: {values}")

    print("\n▶ WISC-V 소검사 환산점수")
    subtest_scores = extract_wisc_subtest_scores(pdf_path)
    for k, v in subtest_scores.items():
        print(f"{k} = {v}")

    # ✅ 테스트 변수 출력
    print("\n📌 변수 테스트")
    print(f"언어이해_지표점수 = {언어이해_지표점수}")
    print(f"전체IQ_백분위 = {전체IQ_백분위}")
    print(f"유동추론_신뢰구간 = {유동추론_신뢰구간}")
    print(f"언어이해_공통성 = {언어이해_공통성}")
    print(f"시공간_퍼즐 = {시공간_퍼즐}")
