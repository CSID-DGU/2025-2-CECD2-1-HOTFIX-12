"""
DART 공시 데이터 추출 메인 스크립트
특정 기업의 공시 문서 조회하고 HTML을 파싱하여 구조화된 JSON으로 저장
"""

import os
import json
from datetime import datetime, timedelta
from dart_api import get_disclosure_list, get_disclosure_detail
from parsers import parser_earnings, parser_rights_issue


def main():
    # 설정
    CORP_CODE = "00126380"  # 삼성전자 고유번호
    
    # 조회 기간 설정 (최근 1년)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    begin_de = start_date.strftime('%Y%m%d')
    end_de = end_date.strftime('%Y%m%d')
    
    print(f"=" * 80)
    print(f"DART 공시 데이터 추출 시작")
    print(f"조회 기간: {begin_de} ~ {end_de}")
    print(f"=" * 80)
    
    # 출력 디렉토리 생성
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 공시 목록 조회
    print("\n[1] 공시 목록 조회 중...")
    disclosure_list = get_disclosure_list(
        corp_code=CORP_CODE,
        begin_de=begin_de,
        end_de=end_de,
        pblntf_ty='A'  # 정기공시
    )
    
    if not disclosure_list:
        print("공시 목록을 가져올 수 없습니다.")
        return
    
    print(f"총 {len(disclosure_list)}건의 공시를 발견했습니다.")
    
    # 대상 보고서 유형 정의
    target_reports = {
        '반기보고서': parser_earnings,
        '분기보고서': parser_earnings,
        '유상증자결정': parser_rights_issue
    }
    
    # 처리 통계
    stats = {
        'total_processed': 0,
        'success': 0,
        'failed': 0,
        'skipped': 0
    }
    
    # 공시 목록 순회
    print("\n[2] 대상 공시 처리 중...")
    print("-" * 80)
    
    for idx, report in enumerate(disclosure_list, 1):
        report_nm = report.get('report_nm', '')
        rcept_no = report.get('rcept_no', '')
        rcept_dt = report.get('rcept_dt', '')
        
        # 대상 보고서인지 확인
        parser_module = None
        report_type = None
        
        for target, parser in target_reports.items():
            if target in report_nm:
                parser_module = parser
                report_type = target
                break
        
        if not parser_module:
            continue
        
        stats['total_processed'] += 1
        
        print(f"\n[{stats['total_processed']}] {report_nm}")
        print(f"    접수번호: {rcept_no}")
        print(f"    접수일자: {rcept_dt}")
        
        # 상세 내용 조회
        print(f"    → HTML 다운로드 중...")
        html_content = get_disclosure_detail(rcept_no)
        
        if not html_content:
            print(f"    ✗ HTML 다운로드 실패")
            stats['failed'] += 1
            continue
        
        # 임시로 XML 파일 저장 (디버깅용)
        xml_path = os.path.join(output_dir, f"{rcept_no}.xml")
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 파싱 실행
        # """추후 NER 모델로 연결할 부분"""
        print(f"    → {report_type} 파싱 중...")
        parsed_data = parser_module.parse(html_content)
        
        if not parsed_data:
            print(f"    ✗ 파싱 실패 - 필수 데이터를 찾을 수 없습니다.")
            stats['failed'] += 1
            continue
        
        # JSON 파일 저장
        json_path = os.path.join(output_dir, f"{rcept_no}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=4)
        
        print(f"    ✓ JSON 저장 완료: {json_path}")
        
        # XML 파일 삭제
        if os.path.exists(xml_path):
            os.remove(xml_path)
            print(f"    ✓ 임시 XML 파일 삭제")
        
        stats['success'] += 1
    
    # 최종 결과 출력
    print("\n" + "=" * 80)
    print("처리 완료")
    print("=" * 80)
    print(f"처리 대상: {stats['total_processed']}건")
    print(f"성공: {stats['success']}건")
    print(f"실패: {stats['failed']}건")
    print(f"출력 디렉토리: {os.path.abspath(output_dir)}")
    print("=" * 80)


if __name__ == "__main__":
    main()

