"""
GET /api/consent_get?token=xxx
consent-sign.html용 — HMAC 토큰을 검증하고 신원/폼 메타데이터를 반환.
서명(이미지)은 토큰에 없으며 반환하지 않는다. DB 조회 없음.
"""
import json
import os
import sys
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _consent_token import verify_token


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
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            token = (qs.get('token') or [None])[0]
            if not token:
                return _resp(self, 400, {'error': 'token required'})

            payload, reason = verify_token(token)
            if not payload:
                if reason == 'expired':
                    return _resp(self, 410, {'error': '링크가 만료되었습니다 / Link expired'})
                return _resp(self, 404, {'error': '링크가 잘못되었습니다 / Invalid link'})

            return _resp(self, 200, {
                'consent_type': payload.get('ct'),
                'child_first_name': payload.get('fn'),
                'child_last_name': payload.get('ln'),
                'child_name': payload.get('cn'),
                'child_dob': payload.get('dob'),
                'gender': payload.get('g'),
                'parent_name': payload.get('pn'),
                'restrictions': payload.get('rest'),
                'consent_version': payload.get('ver'),
                'language': payload.get('lang'),
            })

        except Exception as e:
            return _resp(self, 500, {'error': str(e)})
