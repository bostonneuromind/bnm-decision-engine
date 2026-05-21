import io
p = 'public/beta-signup.html'
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """document.querySelectorAll('input[name="parentLocation"]').forEach(r => {
  r.addEventListener('change', toggleParentEmailRequired);
});
// 초기 상태도 반영
toggleParentEmailRequired();"""

new = """document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('input[name="parentLocation"]').forEach(r => {
    r.addEventListener('change', toggleParentEmailRequired);
    r.addEventListener('click', toggleParentEmailRequired);
  });
  toggleParentEmailRequired();
});"""

if old in s:
    s = s.replace(old, new)
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)
    print('done')
else:
    print('OLD NOT FOUND')
