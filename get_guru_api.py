from dotenv import load_dotenv
import os
import requests
import time

# 1. 환경 변수 로드
load_dotenv()
api_key = os.getenv("API_KEY")

# 2. 설정 (삼성전자)
stock_code = "005930"
url = f"https://api.guruwhisper.com/api/v1/korfsextract?code={stock_code}&apikey={api_key}"

# 3. 데이터 요청
try:
    response = requests.get(url)
    response.raise_for_status() # HTTP 에러 체크
    data = response.json()
except Exception as e:
    print(f"API 요청 중 오류 발생: {e}")
    exit()

# 데이터 키 확인
if "data" not in data:
    print("데이터가 없습니다. API 응답을 확인하세요.")
    exit()

rows = data["data"]

# [중요 1] 날짜 기준 오름차순(과거 -> 최신) 정렬
# API 데이터 순서가 섞여있을 수 있으므로, 과거부터 차례대로 계산하기 위해 정렬합니다.
rows.sort(key=lambda x: x["tgdate"])

result = []
# 이동평균 계산을 위한 임시 리스트
operating_ratio_list = []
net_ratio_list = []

print(f"[{stock_code}] 데이터 분석 시작... (총 {len(rows)}개 분기)")

for item in rows:
    tgdate = item.get("tgdate", "") # 실적 기준일
    revenue = item.get("revenue", 0) # 매출
    operatingIncome = item.get("operatingIncome", 0) # 영업이익
    netIncome = item.get("netIncome", 0) # 순이익
    
    # [안전장치] 매출이 0이거나 None이면 나눗셈 불가 (0으로 처리)
    if revenue and revenue > 0:
        op_ratio = (operatingIncome / revenue) * 100
        net_ratio = (netIncome / revenue) * 100
    else:
        op_ratio = 0.0
        net_ratio = 0.0

    # 리스트에 비율 추가
    operating_ratio_list.append(op_ratio)
    net_ratio_list.append(net_ratio)

    # [중요 2] 최근 4분기 이동 평균 계산 (Trailing 4 Quarters)
    # 슬라이싱 [-4:]는 데이터가 4개 미만일 땐 전체 평균, 4개 이상일 땐 뒤에서 4개 평균을 구함
    if len(operating_ratio_list) > 0:
        op_ratio_avg4 = sum(operating_ratio_list[-4:]) / len(operating_ratio_list[-4:])
        net_ratio_avg4 = sum(net_ratio_list[-4:]) / len(net_ratio_list[-4:])
    else:
        op_ratio_avg4 = 0.0
        net_ratio_avg4 = 0.0

    result.append({
        "tgdate": tgdate,
        "revenue": revenue,
        "operatingIncome": operatingIncome,
        "netIncome": netIncome,
        "operatingIncomeRatio": op_ratio,
        "operatingIncomeRatioAvg4": op_ratio_avg4,
        "netIncomeRatio": net_ratio,
        "netIncomeRatioAvg4": net_ratio_avg4,
    })

# [중요 3] 결과 출력: 가장 최근 데이터 5개를 확인하려면 뒤에서부터 슬라이싱([-5:])해야 합니다.
print("\n" + "=" * 80)
print(f"{'기준일':<12} | {'매출(단위:원)':>15} | {'영업이익률':>10} | {'4분기평균':>10} | {'순이익률':>10}")
print("=" * 80)

if result:
    # 최근 5개 분기 출력
    for r in result[-5:]:
        print(f"{r['tgdate']:<12} | "
              f"{r['revenue']:>15,.0f} | "
              f"{r['operatingIncomeRatio']:>9.2f}% | "
              f"{r['operatingIncomeRatioAvg4']:>9.2f}% | "
              f"{r['netIncomeRatio']:>9.2f}%")
else:
    print("출력할 결과가 없습니다.")

print("=" * 80)

# 마지막으로 가장 최근 분기의 핵심 지표 요약
if result:
    latest = result[-1]
    print(f"\n[최신 요약 - {latest['tgdate']}]")
    print(f"▶ 최근 분기 영업이익률: {latest['operatingIncomeRatio']:.2f}%")
    print(f"▶ 최근 1년(4분기) 평균 영업이익률: {latest['operatingIncomeRatioAvg4']:.2f}% (기초체력)")

time.sleep(5)