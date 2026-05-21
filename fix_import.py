import io
p = 'api/self_sign.py'
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# import 이름 수정
s = s.replace('from _resend import send_parent_consent_email', 'from _resend import parent_consent_email')

# 함수 호출 이름도 수정
s = s.replace('send_parent_consent_email(', 'parent_consent_email(')

with io.open(p, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
print('done')
