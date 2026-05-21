"""
POST /api/beta_signup
베타 신청자 등록
"""
import json
import secrets
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler
import sys
import os

# api/ 폴더의 입력
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase import insert
from _resend import parent_consent_email


def _json_response(handler, status, body):
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.end_headers()
    handler.wfile.write(json.dumps(body).encode('utf-8'))


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length).decode('utf-8')
            data = json.loads(raw) if raw else {}

            # 필수 입력
            full_name = (data.get('fullName') or '').strip()
            email = (data.get('email') or '').strip().lower()
            birth_date = data.get('birthDate')
            age = data.get('age')
            is_minor = bool(data.get('isMinor'))
            language = data.get('language', 'ko')

            if not full_name or not email or not birth_date or age is None:
                return _json_response(self, 400, {'error': '필수 불러오는 중'})

            # 입력
            signup_row = {
                'full_name': full_name,
                'email': email,
                'phone': (data.get('phone') or '').strip() or None,
                'birth_date': birth_date,
                'age': int(age),
                'is_minor': is_minor,
                'language': language,
                'status': 'pending',
            }

            parent_present = bool(data.get('parentPresent'))
            parent_email = (data.get('parentEmail') or '').strip().lower() or None

            if is_minor:
                signup_row.update({
                    'parent_present_in_clinic': parent_present,
                    'parent_name': (data.get('parentName') or '').strip() or None,
                    'parent_email': parent_email,
                    'parent_phone': (data.get('parentPhone') or '').strip() or None,
                    'parent_relationship': data.get('parentRelationship') or None,
                })

                if not parent_present and parent_email:
                    # 이메일 진행 중
                    token = secrets.token_urlsafe(32)
                    expires = datetime.now(timezone.utc) + timedelta(days=7)
                    signup_row['parent_consent_token'] = token
                    signup_row['parent_consent_token_expires_at'] = expires.isoformat()

            # Supabase 자료
            result = insert('beta_signups', signup_row)
            signup_id = result['id']

            # 미성년 + 이메일 입력 → 부모에게 이메일 전송
            if is_minor and not parent_present and parent_email:
                site_url = os.environ.get('SITE_URL', 'https://decision.neurocatchers.com').rstrip('/')
                consent_url = f"{site_url}/parent-consent.html?token={result['parent_consent_token']}&lang={language}"
                try:
                    parent_consent_email(
                        parent_name=result.get('parent_name', ''),
                        parent_email=parent_email,
                        child_name=full_name,
                        child_age=age,
                        consent_url=consent_url,
                        language=language
                    )
                    # 불러오는 중
                    from _supabase import update as sb_update
                    sb_update('beta_signups', {'id': f'eq.{signup_id}'}, {
                        'parent_email_sent_at': datetime.now(timezone.utc).isoformat(),
                        'status': 'parent_email_sent'
                    })
                except Exception as e:
                    # 이메일 진행 중 자료
                    print(f"Email send failed: {e}")

            # 감사 로그
            try:
                insert('beta_consent_log', {
                    'signup_id': signup_id,
                    'event_type': 'signup_created',
                    'event_data': {
                        'age': age,
                        'is_minor': is_minor,
                        'parent_present': parent_present,
                    },
                    'ip_address': self.headers.get('X-Forwarded-For', '').split(',')[0].strip() or None,
                    'user_agent': self.headers.get('User-Agent', '')[:500],
                })
            except Exception as e:
                print(f"Audit log failed: {e}")

            return _json_response(self, 200, {
                'success': True,
                'signup_id': signup_id,
                'is_minor': is_minor,
                'parent_present': parent_present,
            })

        except Exception as e:
            print(f"beta_signup error: {e}")
            return _json_response(self, 500, {'error': str(e)})
