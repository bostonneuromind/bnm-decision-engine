import io
p = 'public/beta-signup.html'
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1. 부모 이메일 라벨에 id 추가 (별표 토글용)
old1 = '<label>부모/보호자 이메일 <span class="required">*</span></label>'
new1 = '<label id="parentEmailLabel">부모/보호자 이메일 <span class="required" id="parentEmailStar">*</span></label>'
s = s.replace(old1, new1)

# 2. 이메일 필수 검증 분기 처리 (parentPresent일 때는 이메일 optional)
old2 = '''    if (!parentName || !parentEmail || !parentRel) {
      showError('부모/보호자 정보를 모두 박아주세요');'''
new2 = '''    const isParentPresent = radio.value === 'present';
    if (!parentName || !parentRel || (!isParentPresent && !parentEmail)) {
      showError(isParentPresent ? '부모/보호자 성명과 관계를 입력해주세요' : '부모/보호자 정보를 모두 입력해주세요');'''
s = s.replace(old2, new2)

# 3. 라디오 변경 시 별표 토글 — 스크립트 끝에 추가
toggle_script = '''
// 부모 현장 여부에 따라 이메일 별표 토글
function toggleParentEmailRequired() {
  const radio = document.querySelector('input[name="parentLocation"]:checked');
  const star = document.getElementById('parentEmailStar');
  const emailInput = document.getElementById('parentEmail');
  if (!radio || !star) return;
  if (radio.value === 'present') {
    star.style.display = 'none';
    if (emailInput) emailInput.placeholder = 'parent@example.com (선택사항)';
  } else {
    star.style.display = '';
    if (emailInput) emailInput.placeholder = 'parent@example.com';
  }
}
document.querySelectorAll('input[name="parentLocation"]').forEach(r => {
  r.addEventListener('change', toggleParentEmailRequired);
});
// 초기 상태도 반영
toggleParentEmailRequired();
'''
# </script> 직전에 박기
s = s.replace('</script>', toggle_script + '\n</script>', 1)

with io.open(p, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
print('done')
