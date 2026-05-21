"""
POST /api/feedback
피드백 내용
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase import insert


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

            row = {
                'signup_id': data.get('signup_id') or None,
                'rating': int(data.get('rating', 0)) if data.get('rating') else None,
                'category': data.get('category'),
                'comment': (data.get('comment') or '').strip() or None,
                'would_recommend': data.get('would_recommend'),
                'language': data.get('language', 'ko'),
                'page_url': data.get('page_url'),
                'session_data': data.get('session_data'),
            }
            insert('beta_feedback', row)
            return _resp(self, 200, {'success': True})

        except Exception as e:
            print(f"feedback error: {e}")
            return _resp(self, 500, {'error': str(e)})
