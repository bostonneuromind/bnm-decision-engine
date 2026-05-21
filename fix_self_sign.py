import io
p = 'api/self_sign.py'
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1. import에 _resend, secrets 추가
old_import = "from _supabase import select, update, insert"
new_import = """import secrets
from datetime import timedelta
from _supabase import select, update, insert
from _resend import send_parent_consent_email"""
s = s.replace(old_import, new_import)

# 2. minor_assent + 부모 remote일 때 이메일 발송
old_logic = """            elif mode == 'minor_assent':
                new_status = 'parent_email_sent' if row.get('parent_email_sent_at') else 'self_signed'

            update('beta_signups', {'id': f'eq.{signup_id}'}, {
                'self_signed_at': now,
                'self_signature_data': signature,
                'self_ip': ip,
                'status': new_status,
            })"""

new_logic = """            elif mode == 'minor_assent':
                # 부모가 현장에 없으면 이메일 발송 필요
                parent_present = row.get('parent_present_in_clinic', False)
                if parent_present:
                    new_status = 'self_signed'  # 현장에서 부모 사인 대기
                else:
                    new_status = 'parent_email_sent'

            update_fields = {
                'self_signed_at': now,
                'self_signature_data': signature,
                'self_ip': ip,
                'status': new_status,
            }

            # minor + remote parent: 토큰 생성 + 이메일 발송
            if mode == 'minor_assent' and new_status == 'parent_email_sent':
                token = secrets.token_urlsafe(32)
                expires = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
                update_fields['parent_consent_token'] = token
                update_fields['parent_consent_token_expires_at'] = expires
                update_fields['parent_email_sent_at'] = now

                # Resend 이메일 발송
                try:
                    send_parent_consent_email(
                        parent_email=row.get('parent_email'),
                        parent_name=row.get('parent_name'),
                        child_name=row.get('full_name'),
                        child_age=row.get('age'),
                        consent_token=token,
                        language=row.get('language', 'ko'),
                    )
                    print(f"parent consent email sent to {row.get('parent_email')}")
                except Exception as email_err:
                    print(f"email send failed: {email_err}")
                    # 이메일 실패해도 status는 업데이트 (재발송 가능)

            update('beta_signups', {'id': f'eq.{signup_id}'}, update_fields)"""

s = s.replace(old_logic, new_logic)

with io.open(p, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
print('done')
