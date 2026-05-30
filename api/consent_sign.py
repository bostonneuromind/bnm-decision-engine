"""
POST /api/consent_sign
이메일 서명 페이지에서 canvas 서명 제출 → HMAC 토큰 검증 → consent_records insert.
consent_records의 실재 컬럼만 사용(consent_text/status/token 컬럼 없음).
signature가 NOT NULL이므로 서명 완료 시점에만 row가 생성된다.
토큰은 self-contained(재사용 가능)이므로 동일 신원의 중복 insert를 막는다.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _consent_token import verify_token
from _supabase import select, insert

DATA_TYPES_DEFAULT = ['survey', 'qEEG', 'HRV', 'ERP', 'typing_dynamics',
                      'ai_conversation', 'assessment_differential', 'future']


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

            token = data.get('token')
            signature = data.get('signature')
            if not token:
                return _resp(self, 400, {'error': 'token required'})
            if not signature:
                return _resp(self, 400, {'error': 'signature required'})

            payload, reason = verify_token(token)
            if not payload:
                if reason == 'expired':
                    return _resp(self, 410, {'error': '링크가 만료되었습니다 / Link expired'})
                return _resp(self, 404, {'error': '링크가 잘못되었습니다 / Invalid link'})

            parent_email = (payload.get('pe') or '').strip().lower()
            child_name = (payload.get('cn') or '').strip()

            # 재사용 방지 — 동일 신원의 이메일 서명이 이미 있으면 중복 insert 금지
            existing = select(
                'consent_records',
                filters={
                    'parent_email': f'eq.{parent_email}',
                    'child_name': f'eq.{child_name}',
                    'sign_method': 'eq.email',
                    'signed_from': 'eq.bostonneuromind',
                },
                columns='id',
            )
            if existing:
                return _resp(self, 409, {'error': '이미 서명되었습니다 / Already signed'})

            now = datetime.now(timezone.utc)
            valid_until = now + timedelta(days=365)

            row = {
                'consent_type': payload.get('ct'),
                'child_name': child_name,
                'child_first_name': (payload.get('fn') or '').strip() or None,
                'child_last_name': (payload.get('ln') or '').strip() or None,
                'child_dob': payload.get('dob') or None,
                'gender': (payload.get('g') or '').strip() or None,
                'parent_name': (payload.get('pn') or '').strip() or None,
                'parent_email': parent_email,
                'signature': signature,
                'sign_method': 'email',
                'restrictions': (payload.get('rest') or '').strip() or None,
                'scope': 'all_platforms',
                'data_types': payload.get('dt') or DATA_TYPES_DEFAULT,
                'consent_version': payload.get('ver') or 'v1',
                'signed_at': now.isoformat(),
                'expires_at': valid_until.isoformat(),
                'signed_from': 'bostonneuromind',
            }

            result = insert('consent_records', row)
            return _resp(self, 200, {'success': True, 'id': result.get('id') if result else None})

        except Exception as e:
            import traceback
            print(f"consent_sign error: {e}")
            print(traceback.format_exc())
            return _resp(self, 500, {'error': str(e)})
