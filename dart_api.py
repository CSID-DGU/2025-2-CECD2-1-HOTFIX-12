"""
DART API 통신 모듈
전자공시시스템(DART) OpenAPI로 공시 정보 조회
"""

import os
import requests
from typing import List, Dict, Optional

# 환경 변수 로드 (dotenv 없이 직접 처리)
def load_env():
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # 따옴표 제거
                    value = value.strip('\'"')
                    os.environ[key.strip()] = value

# 환경 변수 로드
load_env()

# API 설정
DART_API_KEY = os.getenv('DART_API_KEY')
BASE_URL = 'https://opendart.fss.or.kr/api'


def get_disclosure_list(
    corp_code: str,
    begin_de: str,
    end_de: str,
    pblntf_ty: str = 'A'
) -> Optional[List[Dict]]:
    """
    공시 목록 조회
    
    Args:
        corp_code: 고유번호 (8자리)
        begin_de: 시작일 (YYYYMMDD)
        end_de: 종료일 (YYYYMMDD)
        pblntf_ty: 공시유형 (A: 정기공시, B: 주요사항보고, C: 발행공시, D: 지분공시, E: 기타공시, F: 외부감사관련, G: 펀드공시, H: 자산유동화, I: 거래소공시, J: 공정위공시)
    
    Returns:
        공시 목록 리스트 또는 None
    """
    url = f'{BASE_URL}/list.json'
    
    params = {
        'crtfc_key': DART_API_KEY,
        'corp_code': corp_code,
        'bgn_de': begin_de,
        'end_de': end_de,
        'pblntf_ty': pblntf_ty,
        'page_count': 100
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == '000':
            return data.get('list', [])
        else:
            print(f"API 오류: {data.get('message')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"요청 오류: {e}")
        return None


def get_disclosure_detail(rcept_no: str) -> Optional[str]:
    """
    공시 상세 내용(HTML) 조회
    
    Args:
        rcept_no: 접수번호 (14자리)
    
    Returns:
        HTML 문자열 또는 None
    """
    url = f'{BASE_URL}/document.xml'
    
    params = {
        'crtfc_key': DART_API_KEY,
        'rcept_no': rcept_no
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # 다양한 인코딩 시도
        content = response.content
        
        # 인코딩 감지 및 변환
        encodings_to_try = ['utf-8', 'euc-kr', 'cp949', 'iso-8859-1']
        
        for encoding in encodings_to_try:
            try:
                decoded_content = content.decode(encoding)
                # 한글이 제대로 디코딩되었는지 확인
                if '매출액' in decoded_content or '영업이익' in decoded_content or '손익계산서' in decoded_content:
                    return decoded_content
            except UnicodeDecodeError:
                continue
        
        # 모든 인코딩이 실패하면 utf-8로 강제 변환 (에러 무시)
        return content.decode('utf-8', errors='ignore')
        
    except requests.exceptions.RequestException as e:
        print(f"상세 조회 오류: {e}")
        return None

