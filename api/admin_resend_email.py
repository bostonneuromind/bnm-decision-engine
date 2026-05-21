"""POST /api/admin_resend_email — Admin 부모 동의 이메일 재발송"""
import json
import os
import sys
import secrets
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase import select, update, insert
from _resend import parent_consent_email


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
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Admin-Password')
        self.end_headers()

    def do_POST(self):
        admin_pw = self.headers.get('X-Admin-Password', '')
        if admin_pw != 'bnm1#':
            return _resp(self, 401, {'error': 'Unauthorized'})

        try:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))
            signup_id = data.get('signup_id')

            if not signup_id:
                return _resp(self, 400, {'error': 'signup_id required'})

            row = select('beta_signups', filters={'id': f'eq.{signup_id}'}, single=True)
            if not row:
                return _resp(self, 404, {'error': 'Signup not found'})

            if not row.get('is_minor'):
                return _resp(self, 400, {'error': 'Not a minor signup'})

            if not row.get('parent_email'):
                return _resp(self, 400, {'error': 'No parent email on file'})

            new_token = secrets.token_urlsafe(32)
            now = datetime.now(timezone.utc)
            expires = (now + timedelta(days=7)).isoformat()

            update_fields = {
                'parent_consent_token': new_token,
                'parent_consent_token_expires_at': expires,
                'parent_email_sent_at': now.isoformat(),
                'status': 'parent_email_sent',
            }

            site_url = os.environ.get('SITE_URL', 'https://decision.neurocatchers.com')
            language = row.get('language', 'ko')
            consent_url = f"{site_url}/parent-consent.html?token={new_token}&lang={language}"

            parent_consent_email(
                parent_name=row.get('parent_name'),
                parent_email=row.get('parent_email'),
                child_name=row.get('full_name'),
                child_age=row.get('age'),
                consent_url=consent_url,
                language=language,
            )

            update('beta_signups', {'id': f'eq.{signup_id}'}, update_fields)

            ip = self.headers.get('X-Forwarded-For', '').split(',')[0].strip() or None
            insert('beta_consent_log', {
                'signup_id': signup_id,
                'event_type': 'admin_email_resent',
                'event_data': {'parent_email': row.get('parent_email')},
                'ip_address': ip,
                'user_agent': self.headers.get('User-Agent', '')[:500],
            })

            return _resp(self, 200, {'success': True, 'parent_email': row.get('parent_email')})

        except Exception as e:
            print(f"admin_resend_email error: {e}")
            return _resp(self, 500, {'error': str(e)})
