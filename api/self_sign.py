"""
POST /api/self_sign
본인 서명 자료 (성인 동의 또는 미성년자 Assent)
"""
import json
import os
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase import select, update, insert


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
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            signup_id = data.get('signup_id')
            signature = data.get('signature')
            mode = data.get('mode', 'adult')

            if not signup_id or not signature:
                return _resp(self, 400, {'error': 'signup_id and signature required'})

            row = select('beta_signups', filters={'id': f'eq.{signup_id}'}, single=True)
            if not row:
                return _resp(self, 404, {'error': 'Signup not found'})

            now = datetime.now(timezone.utc).isoformat()
            ip = self.headers.get('X-Forwarded-For', '').split(',')[0].strip() or None

            # 입력
            new_status = row['status']
            if mode == 'adult':
                new_status = 'fully_consented'
            elif mode == 'in_person':
                new_status = 'self_signed'  # 자료 부모 불러오는 중
            elif mode == 'minor_assent':
                new_status = 'parent_email_sent' if row.get('parent_email_sent_at') else 'self_signed'

            update('beta_signups', {'id': f'eq.{signup_id}'}, {
                'self_signed_at': now,
                'self_signature_data': signature,
                'self_ip': ip,
                'status': new_status,
            })

            # 감사 로그
            insert('beta_consent_log', {
                'signup_id': signup_id,
                'event_type': 'self_signed',
                'event_data': {'mode': mode},
                'ip_address': ip,
                'user_agent': self.headers.get('User-Agent', '')[:500],
            })

            return _resp(self, 200, {'success': True, 'status': new_status})

        except Exception as e:
            print(f"self_sign error: {e}")
            return _resp(self, 500, {'error': str(e)})
