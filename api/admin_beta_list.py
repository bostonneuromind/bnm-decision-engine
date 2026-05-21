"""GET /api/admin_beta_list — Admin 전체 베타 신청자 리스트"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase import select


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
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Admin-Password')
        self.end_headers()

    def do_GET(self):
        admin_pw = self.headers.get('X-Admin-Password', '')
        if admin_pw != 'bnm1#':
            return _resp(self, 401, {'error': 'Unauthorized'})

        try:
            # filters로 order/limit 박기 (PostgREST는 query param으로 받음)
            rows = select('beta_signups', filters={
                'order': 'created_at.desc',
                'limit': '200'
            })

            if rows is None:
                rows = []

            stats = {
                'total': len(rows),
                'pending': 0,
                'self_signed': 0,
                'parent_email_sent': 0,
                'fully_consented': 0,
                'minors': 0,
                'adults': 0,
            }
            for r in rows:
                status = r.get('status', 'pending')
                if status in stats:
                    stats[status] += 1
                if r.get('is_minor'):
                    stats['minors'] += 1
                else:
                    stats['adults'] += 1

            return _resp(self, 200, {
                'success': True,
                'signups': rows,
                'stats': stats
            })

        except Exception as e:
            import traceback
            print(f"admin_beta_list error: {e}")
            print(traceback.format_exc())
            return _resp(self, 500, {'error': str(e)})
