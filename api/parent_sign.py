"""
POST /api/parent_sign
부모/보호자 서명 자료
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
            token = data.get('token')
            signature = data.get('signature')

            if not signature:
                return _resp(self, 400, {'error': 'signature required'})

            # 진행 중
            if token:
                row = select('beta_signups', filters={'parent_consent_token': f'eq.{token}'}, single=True)
                if not row:
                    return _resp(self, 404, {'error': '링크가 만료되었거나 잘못되었습니다 / Invalid or expired link'})
                expires_str = row.get('parent_consent_token_expires_at')
                if expires_str:
                    expires = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                    if datetime.now(timezone.utc) > expires:
                        return _resp(self, 410, {'error': '링크가 만료되었습니다 / Link expired'})
                signup_id = row['id']
            elif signup_id:
                row = select('beta_signups', filters={'id': f'eq.{signup_id}'}, single=True)
                if not row:
                    return _resp(self, 404, {'error': 'Signup not found'})
            else:
                return _resp(self, 400, {'error': 'signup_id or token required'})

            now = datetime.now(timezone.utc).isoformat()
            ip = self.headers.get('X-Forwarded-For', '').split(',')[0].strip() or None

            # 부모 서명 자료, 입력하세요
            new_status = 'fully_consented' if row.get('self_signed_at') else 'parent_signed'

            update('beta_signups', {'id': f'eq.{signup_id}'}, {
                'parent_signed_at': now,
                'parent_signature_data': signature,
                'parent_ip': ip,
                'status': new_status,
                # 진행 중 (자료 보안)
                'parent_consent_token': None,
                'parent_consent_token_expires_at': None,
            })

            # 감사 로그
            insert('beta_consent_log', {
                'signup_id': signup_id,
                'event_type': 'parent_signed',
                'event_data': {'via_token': bool(token)},
                'ip_address': ip,
                'user_agent': self.headers.get('User-Agent', '')[:500],
            })

            return _resp(self, 200, {'success': True, 'status': new_status})

        except Exception as e:
            print(f"parent_sign error: {e}")
            return _resp(self, 500, {'error': str(e)})
