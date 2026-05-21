"""
Supabase Python 헬퍼
Decision Catcher Beta System
"""
import os
import urllib.request
import urllib.parse
import json

SUPABASE_URL = os.environ.get('SUPABASE_URL', '').rstrip('/')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')


def _request(method, path, payload=None, params=None, prefer=None):
    """Supabase REST API 호출"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL or SUPABASE_KEY not configured")

    url = f"{SUPABASE_URL}/rest/v1{path}"
    if params:
        url += '?' + urllib.parse.urlencode(params)

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
    }
    if prefer:
        headers['Prefer'] = prefer

    data = None
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            if body:
                return json.loads(body)
            return None
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8') if e.fp else str(e)
        raise RuntimeError(f"Supabase {method} {path} failed ({e.code}): {err_body}")


def insert(table, data):
    """단일 row 삽입 — 박은 row 반환"""
    result = _request('POST', f'/{table}', payload=data, prefer='return=representation')
    return result[0] if isinstance(result, list) and result else result


def select(table, filters=None, columns='*', single=False):
    """조회 — filters는 {'column': 'eq.value'} 형식"""
    params = {'select': columns}
    if filters:
        params.update(filters)
    result = _request('GET', f'/{table}', params=params)
    if single and isinstance(result, list):
        return result[0] if result else None
    return result


def update(table, filters, data):
    """업데이트"""
    params = {}
    if filters:
        params.update(filters)
    result = _request('PATCH', f'/{table}', payload=data, params=params, prefer='return=representation')
    return result
