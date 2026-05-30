"""
POST /api/consent_email
Boston Neuromind 연구·임상 동의서 — 이메일 서명 경로(시작).
폼 메타데이터를 HMAC 토큰(7일 만료)에 담아 서명 링크 이메일 발송.
consent_records에는 아무것도 쓰지 않는다(서명 완료 시 consent_sign이 insert).
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _consent_token import make_token
from _resend import consent_request_email


def _resp(h, status, body):
    h.send_response(status)
    h.send_header('Content-Type', 'application/json; charset=utf-8')
    h.send_header('Access-Control-Allow-Origin', '*')
    h.end_headers()
    h.wfile.write(json.dumps(body).encode('utf-8'))


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

            consent_type = data.get('consent_type')
            first = (data.get('child_first_name') or '').strip()
            last = (data.get('child_last_name') or '').strip()
            child_dob = data.get('child_dob')
            recipient_email = (data.get('recipient_email') or '').strip().lower()
            recipient_name = (data.get('recipient_name') or '').strip()
            language = 'en' if data.get('language') == 'en' else 'ko'

            if consent_type not in ('adult', 'minor'):
                return _resp(self, 400, {'error': 'invalid consent_type'})
            if not first or not last or not child_dob:
                return _resp(self, 400, {'error': 'name and date of birth required'})
            if not recipient_email or '@' not in recipient_email:
                return _resp(self, 400, {'error': 'valid recipient email required'})

            # parent_email은 consent_records에서 NOT NULL → 항상 recipient_email로 채운다
            token_payload = {
                'ct': consent_type,
                'fn': first,
                'ln': last,
                'cn': (data.get('child_name') or (first + ' ' + last)).strip(),
                'dob': child_dob,
                'g': (data.get('gender') or '').strip(),
                'pn': (data.get('parent_name') or '').strip(),
                'pe': recipient_email,
                'rest': (data.get('restrictions') or '').strip(),
                'ver': data.get('consent_version') or 'v1',
                'dt': data.get('data_types') or [],
                'lang': language,
            }
            token = make_token(token_payload)

            site_url = os.environ.get('SITE_URL', 'https://decision.neurocatchers.com').rstrip('/')
            consent_url = f"{site_url}/consent-sign.html?token={token}&lang={language}"

            consent_request_email(
                to_email=recipient_email,
                display_name=recipient_name or token_payload['pn'] or token_payload['cn'],
                consent_url=consent_url,
                language=language,
            )

            return _resp(self, 200, {'success': True})

        except Exception as e:
            import traceback
            print(f"consent_email error: {e}")
            print(traceback.format_exc())
            return _resp(self, 500, {'error': str(e)})
