import io
p = 'public/beta-pending.html'
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

reps = [
    ('부모님 동의 항목', '부모님 동의 대기 중'),
    ('부모님께 동의서 이메일이 불러오는 중.', '부모님께 동의서 이메일을 전송했습니다.'),
    ('베타 참여가 불러오는 중', '베타 참여가 확정됩니다'),
    ('진행 중 입력, support@neurocatchers.com 으로 입력.', '문의사항이 있으시면 support@neurocatchers.com 으로 연락주세요.'),
]
for old, new in reps:
    s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
print('done')
