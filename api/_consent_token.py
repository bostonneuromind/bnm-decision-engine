"""
Self-contained HMAC consent token.

consent_records 테이블에는 토큰/pending 컬럼이 없고 signature가 NOT NULL이라
서명 전 임시 row를 만들 수 없다. 따라서 이메일 서명 경로는 DB pending 없이
폼 메타데이터를 HMAC 서명한 토큰에 담아 운반한다. 서버 시크릿으로 검증하므로
변조 불가, exp로 7일 만료. consent_records에는 서명 완료된 row만 insert된다.
"""
import os
import json
import hmac
import time
import base64
import hashlib


def _secret():
    s = os.environ.get('CONSENT_TOKEN_SECRET') or os.environ.get('SUPABASE_KEY') or os.environ.get('RESEND_API_KEY')
    if not s:
        raise RuntimeError('No secret available for consent token signing')
    return s.encode('utf-8')


def _b64e(raw):
    return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')


def _b64d(s):
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def make_token(payload, ttl_seconds=7 * 24 * 3600):
    """payload(dict)에 exp를 더해 HMAC 서명된 토큰 문자열 반환."""
    body = dict(payload)
    body['exp'] = int(time.time()) + ttl_seconds
    raw = json.dumps(body, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    b = _b64e(raw)
    sig = hmac.new(_secret(), b.encode('ascii'), hashlib.sha256).hexdigest()
    return b + '.' + sig


def verify_token(token):
    """검증 성공 시 payload(dict) 반환. 실패 시 (None, reason)."""
    try:
        b, sig = token.split('.', 1)
    except (ValueError, AttributeError):
        return None, 'malformed'
    expected = hmac.new(_secret(), b.encode('ascii'), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None, 'bad_signature'
    try:
        payload = json.loads(_b64d(b).decode('utf-8'))
    except Exception:
        return None, 'decode_error'
    if int(payload.get('exp', 0)) < int(time.time()):
        return None, 'expired'
    return payload, None
