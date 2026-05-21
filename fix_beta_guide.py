import io
p = 'public/beta-guide.html'
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

reps = [
    ('자료 항상 우선', '항상 우선'),
    ('모든 outcome 자료 기록', '모든 outcome 데이터 기록'),
    ('베타 클라이언트 자격 자료', '베타 클라이언트 자격 기준'),
    ('포함 자료', '포함 기준'),
    ('8주 자료 가능', '8주 참여 가능'),
    ('영어 자료 가능', '영어 의사소통 가능'),
    ('측정 자료 (Polar', '측정 가능 (Polar'),
    ('CPT 자료)', 'CPT 등)'),
    ('제외 자료', '제외 기준'),
    ('증상 자료 수집', '증상 데이터 수집'),
    ('클라이언트 자료 (15분)', '클라이언트 설명 (15분)'),
    ('영역별 자료:', '영역별 평가:'),
    ('각 회기 자료', '각 회기 구성'),
    ('Outcome 자료 입력', 'Outcome 데이터 입력'),
    ('outcome.html</a> 자료:', 'outcome.html</a>에서:'),
    ('Adaptive Re-routing (v7) 자료', 'Adaptive Re-routing (v7) 실행'),
    ('위기 자료가 catch되면', '위기 신호가 catch되면'),
    ('임상가는 다음 자료 catch:', '임상가는 다음을 확인:'),
    ('<th>자료</th>', '<th>위기 유형</th>'),
    ('데이터 수집 자료', '데이터 수집 항목'),
    ('베타 기간 자료 수집:', '베타 기간 중 다음을 수집:'),
    ('모든 위기 자료:', '모든 위기 이벤트:'),
    ('이유 자료 기록', '이유 필수 기록'),
    ('베타 진행 자료, 다음 자료 catch:', '베타 진행 중, 다음 패턴을 확인:'),
    ('부적합한 자료 (override 자료)', '부적합한 경우 (override 빈도)'),
    ('❌ 일치하는 자료', '❌ 일치하지 않는 경우'),
    ('매뉴얼 자료 missing', '매뉴얼 항목 missing'),
    ('베타 후 자료', '베타 후 계획'),
    ('5명 자료 prediction error 자료 분석', '5명 데이터로 prediction error 분석'),
    ('매핑 행렬 자료 보정', '매핑 행렬 가중치 보정'),
    ('DDE 자료 보정', 'DDE 파라미터 보정'),
    ('베타 자료 반영', '베타 결과 반영'),
    ('모든 자료가 자료에 있습니다:', '모든 정보가 다음 위치에 있습니다:'),
]
for old, new in reps:
    s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
print('beta-guide done, remaining:', s.count('자료'))
