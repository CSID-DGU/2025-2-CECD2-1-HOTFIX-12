# DART 공시 데이터 추출 시스템

전자공시시스템(DART)의 HTML 공시 문서를 파싱하여 구조화된 JSON 데이터로 변환하는 자동화 시스템입니다.

## 📋 프로젝트 개요

이 시스템은 DART API를 통해 기업의 공시 문서를 조회하고, 비정형 HTML 데이터를 파싱하여 AI 모델이 활용할 수 있는 표준화된 JSON 형식으로 변환합니다.

### 주요 기능

- ✅ DART API를 통한 공시 목록 자동 조회
- ✅ 특정 보고서 유형 필터링 (반기보고서, 분기보고서, 유상증자결정 등)
- ✅ HTML 파싱을 통한 재무 데이터 추출
- ✅ 구조화된 JSON 파일 자동 생성
- ✅ 확장 가능한 파서 아키텍처

## 🏗️ 프로젝트 구조

```
news-maker/
├── dart_api.py                 # DART API 통신 모듈
├── main.py                     # 메인 실행 스크립트
├── parsers/                    # 파서 패키지
│   ├── __init__.py
│   ├── parser_earnings.py      # 실적보고서 파서
│   └── parser_rights_issue.py  # 유상증자 파서
├── output/                     # 출력 JSON 파일 저장 디렉토리
├── requirements.txt            # Python 의존성
├── .env.example               # 환경 변수 예시
└── README.md                  # 프로젝트 문서
```

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 DART API 키를 입력하세요.

```bash
cp .env.example .env
```

`.env` 파일 내용:
```
DART_API_KEY=your_api_key_here
```

**DART API 키 발급 방법:**
1. [DART 오픈API](https://opendart.fss.or.kr/) 접속
2. 회원가입 및 로그인
3. 인증키 신청 및 발급

### 3. 실행

```bash
python main.py
```

## 📊 지원하는 보고서 유형

### 1. 실적 보고서 (분기/반기보고서)

**추출 데이터:**
- 회사 기본 정보 (회사명, 보고서 유형, 기간)
- 연결손익계산서 (매출액, 영업이익, 당기순이익)
- 사업부문별 정보 (부문별 매출액, 영업이익)

**출력 JSON 구조:**
```json
{
  "report_info": {
    "company_name": "삼성전자주식회사",
    "report_type": "반기보고서",
    "period": "2024년 6월"
  },
  "financials": {
    "unit": "백만원",
    "consolidated_statement": [
      {
        "item": "매출액",
        "current_period_amount": 50000000,
        "previous_period_amount": 45000000,
        "yoy_growth_rate": 11.11
      }
    ]
  },
  "business_segments": [
    {
      "segment_name": "DX부문",
      "revenue": 30000000,
      "operating_profit": 5000000
    }
  ]
}
```

### 2. 유상증자결정 보고서

**추출 데이터:**
- 회사 기본 정보
- 증자 결정 개요 (증자 방식, 신주 수, 발행가액, 발행총액)
- 자금 사용 목적 및 내역
- 주요 일정 (기준일, 상장예정일)

**출력 JSON 구조:**
```json
{
  "report_info": {
    "company_name": "삼성전자주식회사",
    "report_type": "주요사항보고서(유상증자결정)"
  },
  "decision_summary": {
    "offering_type": "주주배정",
    "new_shares_type": "보통주",
    "new_shares_count": 10000000,
    "offering_price": 50000,
    "total_offering_amount": 500000000000
  },
  "purpose_of_funds": {
    "total": 500000000000,
    "breakdown": [
      {
        "purpose": "시설자금",
        "amount": 300000000000
      }
    ]
  },
  "schedule": {
    "record_date": "2024-06-30",
    "listing_date": "2024-08-15"
  }
}
```

## 🔧 커스터마이징

### 새로운 파서 추가하기

1. `parsers/` 디렉토리에 새 파서 파일 생성 (예: `parser_new_report.py`)
2. `parse(html_content: str) -> Optional[Dict]` 함수 구현
3. `parsers/__init__.py`에 새 파서 import
4. `main.py`의 `target_reports` 딕셔너리에 추가

### 조회 대상 변경하기

`main.py`에서 다음 설정을 변경하세요:

```python
# 기업 고유번호 변경
CORP_CODE = "00126380"  # 삼성전자

# 조회 기간 변경
start_date = end_date - timedelta(days=365)  # 1년

# 공시 유형 변경
pblntf_ty='A'  # A: 정기공시, B: 주요사항보고
```

## 📝 기술 스택

- **Python 3.10+**
- **requests**: HTTP API 통신
- **BeautifulSoup4**: HTML 파싱
- **python-dotenv**: 환경 변수 관리
- **lxml**: HTML 파서 엔진

## ⚠️ 주의사항

1. **API 키 보안**: `.env` 파일은 절대 Git에 커밋하지 마세요
2. **API 호출 제한**: DART API는 일일 호출 제한이 있을 수 있습니다
3. **HTML 구조 변경**: 공시 문서의 HTML 구조가 변경되면 파서 수정이 필요할 수 있습니다
4. **데이터 정확성**: 파싱된 데이터는 반드시 원본과 대조하여 검증하세요

## 🐛 문제 해결

### 파싱 실패 시

1. `output/` 디렉토리의 임시 XML 파일 확인 (실패 시 삭제되지 않음)
2. HTML 구조가 예상과 다를 수 있음 - 파서 로직 수정 필요
3. 콘솔 로그에서 구체적인 오류 메시지 확인

### API 오류 시

1. `.env` 파일의 API 키 확인
2. DART API 서비스 상태 확인
3. 네트워크 연결 확인

## 📄 라이선스

이 프로젝트는 교육 및 연구 목적으로 제공됩니다.

## 🤝 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요.

