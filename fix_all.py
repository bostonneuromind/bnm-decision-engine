import io, glob, re

# 진짜 데이터 의미는 유지, placeholder만 교체
# 패턴: "자료 자료 자료..." 같이 연속된 자료는 placeholder

REPLACEMENTS = {
    # 베타 시스템 placeholder 일괄 정리
    '자료 자료 자료 자료 자료 자료 자료': '진행 중',
    '자료 자료 자료 자료 자료 자료': '진행 중',
    '자료 자료 자료 자료 자료': '진행 중',
    '자료 자료 자료 자료': '입력하세요',
    '자료 자료 자료': '불러오는 중',
    '자료 자료': '입력',
    
    # 구체적 컨텍스트
    '참여 제외 자료': '참여 제외 대상',
    '미성년자 자료': '미성년자 섹션',
    '동의 자료': '동의 항목',
    '동의서 자료': '동의서 작성',
    '안전 자료': '안전 프로토콜',
    '학대 의심 자료': '학대 의심 시',
    '자동 자료': '자동 입력',
    '주차별 진행 자료': '주간 진행 상태',
    '주간 진행 자료': '주간 진행 상태',
    '진행 자료 입력': '진행 상태 입력',
    '보조 자료로만': '보조 도구로만',
    '평가 자료': '평가 항목',
    '훈련 자료': '훈련 카드',
    '피드백 자료': '피드백 내용',
    '카테고리 자료': '카테고리 선택',
    '의견 자료': '의견 입력',
    '추천 자료': '추천 여부',
    '제출 자료': '제출하기',
    '결과 자료': '결과 보기',
    '시작 자료': '시작하기',
    '계속 자료': '계속하기',
    '대기 자료': '대기 중',
    '완료 자료': '완료',
    '실패 자료': '실패',
    '오류 자료': '오류 발생',
    '에러 자료': '오류 발생',
    '확인 자료': '확인',
    '취소 자료': '취소',
    '닫기 자료': '닫기',
    '저장 자료': '저장됨',
    '로딩 자료': '로딩 중',
    '검색 자료': '검색',
    '필터 자료': '필터',
    '정렬 자료': '정렬',
    '⏳ 자료': '⏳ 대기 중',
    '✅ 자료': '✅ 완료',
}

# 진짜 데이터 의미인 자료는 손대지 않음
PROTECTED = [
    '임상 자료',  # 임상 데이터 (진짜)
    '익명 자료',  # 익명화된 데이터 (진짜)
    '모든 자료',  # 모든 데이터 (진짜)
    '귀하의 자료',  # 귀하의 데이터 (진짜)
    '본인의 자료',  # 본인의 데이터 (진짜)
    '자녀의 자료',  # 자녀의 데이터 (진짜)
    '연구 자료',  # 연구 자료 (진짜)
    '참고 자료',  # 참고 자료 (진짜)
    '학습 자료',  # 학습 자료 (진짜)
    '교육 자료',  # 교육 자료 (진짜)
]

def protect_then_replace(s):
    # 보호할 표현은 임시 마커로
    markers = {}
    for i, prot in enumerate(PROTECTED):
        marker = f'__PROTECT_{i}__'
        if prot in s:
            s = s.replace(prot, marker)
            markers[marker] = prot
    
    # 일괄 교체
    for old, new in REPLACEMENTS.items():
        s = s.replace(old, new)
    
    # 마커 복원
    for marker, original in markers.items():
        s = s.replace(marker, original)
    
    return s

# clinician-manual-ko.html은 제외 (진짜 임상 매뉴얼)
files = glob.glob('public/*.html') + glob.glob('api/*.py')
files = [f for f in files if 'clinician-manual-ko' not in f and 'clinician-manual-en' not in f]

total_before = 0
total_after = 0
for fp in files:
    with io.open(fp, 'r', encoding='utf-8') as f:
        s = f.read()
    before = s.count('자료')
    if before == 0:
        continue
    new_s = protect_then_replace(s)
    after = new_s.count('자료')
    with io.open(fp, 'w', encoding='utf-8', newline='') as f:
        f.write(new_s)
    total_before += before
    total_after += after
    print(f'{fp}: {before} -> {after}')

print(f'\nTOTAL: {total_before} -> {total_after}')
