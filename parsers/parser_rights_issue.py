"""
유상증자결정 보고서 파서
주요사항보고서(유상증자결정)에서 증자 관련 정보 추출
"""

from bs4 import BeautifulSoup
import re
from typing import Optional, Dict, List
from datetime import datetime


def parse(html_content: str) -> Optional[Dict]:
    """
    유상증자결정 보고서 HTML 파싱해서 데이터 추출
    
    Args:
        html_content: 공시 HTML 문자열
    
    Returns:
        구조화된 유상증자 데이터 딕셔너리 또는 None
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 기본 결과 구조
        result = {
            "report_info": {
                "company_name": "",
                "report_type": "주요사항보고서(유상증자결정)"
            },
            "decision_summary": {
                "offering_type": "",
                "new_shares_type": "",
                "new_shares_count": 0,
                "offering_price": 0,
                "total_offering_amount": 0
            },
            "purpose_of_funds": {
                "total": 0,
                "breakdown": []
            },
            "schedule": {
                "record_date": "",
                "listing_date": ""
            }
        }
        
        # 1. 회사명 추출
        result["report_info"]["company_name"] = extract_company_name(soup)
        
        # 2. 증자 결정 개요 추출
        result["decision_summary"] = extract_decision_summary(soup)
        
        # 3. 자금 사용 목적 추출
        result["purpose_of_funds"] = extract_purpose_of_funds(soup)
        
        # 4. 일정 추출
        result["schedule"] = extract_schedule(soup)
        
        # 필수 데이터 검증
        if result["decision_summary"]["new_shares_count"] == 0:
            print("유상증자 결정 정보를 찾을 수 없습니다.")
            return None
            
        return result
        
    except Exception as e:
        print(f"파싱 오류: {e}")
        return None


def extract_company_name(soup: BeautifulSoup) -> str:
    """회사명 추출"""
    # """추후 NER 모델로 연결할 부분"""
    company_name = ""
    
    try:
        # 다양한 패턴으로 회사명 추출 시도
        patterns = [
            soup.find('title'),
            soup.find(string=re.compile(r'회사명|법인명')),
            soup.find('p', string=re.compile(r'주식회사|㈜'))
        ]
        
        for pattern in patterns:
            if pattern:
                text = pattern.get_text() if hasattr(pattern, 'get_text') else str(pattern)
                match = re.search(r'([\w\(\)]+(?:주식회사|㈜)[\w\(\)]*)', text)
                if match:
                    company_name = match.group(1).strip()
                    break
        
        # 회사명이 없으면 문서 상단에서 찾기
        if not company_name:
            first_p = soup.find('p')
            if first_p:
                text = first_p.get_text()
                if '주식회사' in text or '㈜' in text:
                    company_name = text.strip()
                    
    except Exception as e:
        print(f"회사명 추출 오류: {e}")
    
    return company_name


def clean_number(value: str) -> float:
    """문자열에서 숫자 추출하고 정제"""
    if not value or value == '-':
        return 0
    
    try:
        # 괄호는 음수를 의미
        is_negative = '(' in value and ')' in value
        
        # 숫자와 소수점, 음수 기호만 남김
        cleaned = re.sub(r'[^\d.-]', '', value)
        
        if not cleaned or cleaned == '-':
            return 0
        
        number = float(cleaned)
        
        if is_negative:
            number = -abs(number)
        
        return number
        
    except (ValueError, AttributeError):
        return 0


def extract_decision_summary(soup: BeautifulSoup) -> Dict:
    """유상증자 결정 개요 추출"""
    # """추후 NER 모델로 연결할 부분"""
    summary = {
        "offering_type": "",
        "new_shares_type": "",
        "new_shares_count": 0,
        "offering_price": 0,
        "total_offering_amount": 0
    }
    
    try:
        # 증자 방식 추출
        offering_type_keywords = ['주주배정', '제3자배정', '일반공모', '주주우선공모']
        for keyword in offering_type_keywords:
            if soup.find(string=re.compile(keyword)):
                summary["offering_type"] = keyword
                break
        
        # 신주 종류 추출
        share_type_element = soup.find(string=re.compile(r'신주.*종류|주식.*종류'))
        if share_type_element:
            parent = share_type_element.find_parent('tr')
            if parent:
                cells = parent.find_all(['td', 'th'])
                if len(cells) >= 2:
                    summary["new_shares_type"] = cells[1].get_text(strip=True)
        
        if not summary["new_shares_type"]:
            summary["new_shares_type"] = "보통주"
        
        # 신주 수 추출
        share_count_keywords = ['신주.*수', '발행.*주식.*수', '증자.*주식.*수']
        for keyword in share_count_keywords:
            element = soup.find(string=re.compile(keyword))
            if element:
                parent = element.find_parent('tr')
                if parent:
                    cells = parent.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        value = cells[1].get_text(strip=True)
                        summary["new_shares_count"] = int(clean_number(value))
                        break
        
        # 발행가액 추출
        price_keywords = ['발행가액|주당.*가액', '청약가액', '모집가액']
        for keyword in price_keywords:
            element = soup.find(string=re.compile(keyword))
            if element:
                parent = element.find_parent('tr')
                if parent:
                    cells = parent.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        value = cells[1].get_text(strip=True)
                        summary["offering_price"] = int(clean_number(value))
                        break
        
        # 발행총액 추출
        total_keywords = ['발행총액|납입.*총액', '증자.*총액', '모집.*총액']
        for keyword in total_keywords:
            element = soup.find(string=re.compile(keyword))
            if element:
                parent = element.find_parent('tr')
                if parent:
                    cells = parent.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        value = cells[1].get_text(strip=True)
                        summary["total_offering_amount"] = int(clean_number(value))
                        break
        
        # 총액이 없으면 계산
        if summary["total_offering_amount"] == 0 and summary["new_shares_count"] > 0 and summary["offering_price"] > 0:
            summary["total_offering_amount"] = summary["new_shares_count"] * summary["offering_price"]
            
    except Exception as e:
        print(f"증자 개요 추출 오류: {e}")
    
    return summary


def extract_purpose_of_funds(soup: BeautifulSoup) -> Dict:
    """자금 사용 목적 추출"""
    # """추후 NER 모델로 연결할 부분"""
    purpose = {
        "total": 0,
        "breakdown": []
    }
    
    try:
        # 자금 사용 목적 테이블 찾기
        purpose_keywords = ['자금.*사용.*목적', '조달.*자금.*사용', '증자.*목적']
        
        for keyword in purpose_keywords:
            element = soup.find(string=re.compile(keyword))
            if element:
                # 해당 섹션의 테이블 찾기
                table = element.find_parent('table')
                if not table:
                    # 다음 테이블 찾기
                    parent = element.find_parent()
                    if parent:
                        table = parent.find_next('table')
                
                if table:
                    purpose = parse_purpose_table(table)
                    break
        
        # 테이블을 못 찾은 경우, 전체에서 키워드 검색
        if not purpose["breakdown"]:
            purpose = extract_purpose_by_text(soup)
            
    except Exception as e:
        print(f"자금 사용 목적 추출 오류: {e}")
    
    return purpose


def parse_purpose_table(table) -> Dict:
    """자금 사용 목적 테이블 파싱"""
    purpose = {
        "total": 0,
        "breakdown": []
    }
    
    try:
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
            
            purpose_text = cells[0].get_text(strip=True)
            
            # 헤더나 합계 행 제외
            if not purpose_text or '합계' in purpose_text or '총계' in purpose_text or '사용목적' in purpose_text:
                continue
            
            amount_text = cells[1].get_text(strip=True)
            amount = int(clean_number(amount_text))
            
            if amount > 0:
                purpose["breakdown"].append({
                    "purpose": purpose_text,
                    "amount": amount
                })
        
        # 총액 계산
        purpose["total"] = sum([item["amount"] for item in purpose["breakdown"]])
        
    except Exception as e:
        print(f"목적 테이블 파싱 오류: {e}")
    
    return purpose


def extract_purpose_by_text(soup: BeautifulSoup) -> Dict:
    """텍스트에서 자금 사용 목적 추출"""
    purpose = {
        "total": 0,
        "breakdown": []
    }
    
    try:
        # 일반적인 사용 목적 키워드
        common_purposes = ['운영자금', '시설자금', '채무상환', '연구개발', '설비투자']
        
        for keyword in common_purposes:
            element = soup.find(string=re.compile(keyword))
            if element:
                # 근처에서 금액 찾기
                parent = element.find_parent('tr')
                if parent:
                    cells = parent.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        if keyword in cell.get_text():
                            # 다음 셀에서 금액 찾기
                            if i + 1 < len(cells):
                                amount_text = cells[i + 1].get_text(strip=True)
                                amount = int(clean_number(amount_text))
                                
                                if amount > 0:
                                    purpose["breakdown"].append({
                                        "purpose": keyword,
                                        "amount": amount
                                    })
                                break
        
        # 총액 계산
        purpose["total"] = sum([item["amount"] for item in purpose["breakdown"]])
        
    except Exception as e:
        print(f"텍스트 기반 목적 추출 오류: {e}")
    
    return purpose


def extract_schedule(soup: BeautifulSoup) -> Dict:
    """유상증자 일정 추출"""
    # """추후 NER 모델로 연결할 부분"""
    schedule = {
        "record_date": "",
        "listing_date": ""
    }
    
    try:
        # 기준일 추출
        record_date_keywords = ['기준일|신주배정.*기준일', '주주명부.*폐쇄.*기준일']
        for keyword in record_date_keywords:
            element = soup.find(string=re.compile(keyword))
            if element:
                parent = element.find_parent('tr')
                if parent:
                    cells = parent.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        date_text = cells[1].get_text(strip=True)
                        schedule["record_date"] = format_date(date_text)
                        break
        
        # 상장예정일 추출
        listing_date_keywords = ['상장예정일|신주.*상장.*예정일', '재상장예정일']
        for keyword in listing_date_keywords:
            element = soup.find(string=re.compile(keyword))
            if element:
                parent = element.find_parent('tr')
                if parent:
                    cells = parent.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        date_text = cells[1].get_text(strip=True)
                        schedule["listing_date"] = format_date(date_text)
                        break
                        
    except Exception as e:
        print(f"일정 추출 오류: {e}")
    
    return schedule


def format_date(date_text: str) -> str:
    """날짜 문자열을 YYYY-MM-DD 형식으로 변환"""
    if not date_text or date_text == '-':
        return ""
    
    try:
        # 다양한 날짜 형식 처리
        date_patterns = [
            (r'(\d{4})[년\-\.](\d{1,2})[월\-\.](\d{1,2})', '%Y-%m-%d'),
            (r'(\d{4})(\d{2})(\d{2})', '%Y-%m-%d'),
        ]
        
        for pattern, format_str in date_patterns:
            match = re.search(pattern, date_text)
            if match:
                year = match.group(1)
                month = match.group(2).zfill(2)
                day = match.group(3).zfill(2)
                return f"{year}-{month}-{day}"
        
        return date_text.strip()
        
    except Exception:
        return date_text.strip()

