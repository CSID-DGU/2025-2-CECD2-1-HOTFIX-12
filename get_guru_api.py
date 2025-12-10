from dotenv import load_dotenv
import os
import requests
import time

load_dotenv()
api_key = os.getenv("API_KEY")
stock_code = "005930" # 기업코드
url = f"https://api.guruwhisper.com/api/v1/korfsextract?code={stock_code}&apikey={api_key}"

response = requests.get(url)
data = response.json()
rows = data["data"]
result = []

# 영업이익률 (영업이익 / 매출 * 100)
operating_ratio_list = []
# 순이익률 (순이익 / 매출 * 100)
net_ratio_list = []

for item in rows:
    tgdate = item["tgdate"] # 실적 기준일
    revenue = item["revenue"] # 분기 매출
    revenueAvg4 = item["revenueAvg4"] # 매출 최근 4분기 평균
    revenueCompare4 = item["revenueCompare4"] # 전년동기대비 매출
    operatingIncome = item["operatingIncome"] # 영업 이익률 (영업이익 / 매출 * 100)
    netIncome = item["netIncome"] # 순이익률 (순이익 / 매출 * 100)
    operatingIncomeRatio = (operatingIncome / revenue * 100) if revenue else None #영업 이익률 최근 4분기 평균
    netIncomeRatio = (netIncome / revenue * 100) if revenue else None # 순이익률 최근 4분기 평균
    
    operating_ratio_list.append(operatingIncomeRatio)
    net_ratio_list.append(netIncomeRatio)

    operatingIncomeRatioAvg4 = (
        sum(operating_ratio_list[-4:]) / len(operating_ratio_list[-4:])
    )
    netIncomeRatioAvg4 = (
        sum(net_ratio_list[-4:]) / len(net_ratio_list[-4:])
    )

    result.append({
        "tgdate": tgdate,
        "revenue": revenue,
        "revenueAvg4": revenueAvg4,
        "revenueCompare4": revenueCompare4,
        "operatingIncomeRatio": operatingIncomeRatio,
        "operatingIncomeRatioAvg4": operatingIncomeRatioAvg4,
        "netIncomeRatio": netIncomeRatio,
        "netIncomeRatioAvg4": netIncomeRatioAvg4,
    })

for r in result[:5]:
    print(r)

time.sleep(5)