"""
GET /api/get_signup?signup_id=xxx 또는 ?token=xxx
신청자 정보 조회 (이름 자동입력용 + 부모 동의서 작성)
"""
import json
import os
import sys
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase import select


def _resp(handler, status, body):
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.end_headers()
    handler.wfile.write(json.dumps(body).encode('utf-8'))


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            signup_id = (qs.get('signup_id') or [None])[0]
            token = (qs.get('token') or [None])[0]

            if not signup_id and not token:
                return _resp(self, 400, {'error': 'signup_id or token required'})

            if token:
                row = select('beta_signups',
                             filters={'parent_consent_token': f'eq.{token}'},
                             single=True)
                if not row:
                    return _resp(self, 404, {'error': '링크가 만료되었거나 잘못되었습니다 / Invalid or expired link'})

                # 입력
                expires_str = row.get('parent_consent_token_expires_at')
                if expires_str:
                    expires = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                    if datetime.now(timezone.utc) > expires:
                        return _resp(self, 410, {'error': '링크가 만료되었습니다 / Link expired'})

                # 진행 중
                return _resp(self, 200, {
                    'full_name': row.get('full_name'),
                    'age': row.get('age'),
                    'parent_name': row.get('parent_name'),
                    'self_signed_at': row.get('self_signed_at'),
                    'parent_signed_at': row.get('parent_signed_at'),
                    'signup_id': row.get('id'),
                })

            # signup_id 자료
            row = select('beta_signups',
                         filters={'id': f'eq.{signup_id}'},
                         columns='id,full_name,age,is_minor,language,parent_name,self_signed_at,parent_signed_at,status',
                         single=True)
            if not row:
                return _resp(self, 404, {'error': 'Not found'})

            return _resp(self, 200, row)

        except Exception as e:
            return _resp(self, 500, {'error': str(e)})
