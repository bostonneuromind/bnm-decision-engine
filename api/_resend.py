"""Resend 이메일 발송 헬퍼"""
import os
import json
import traceback

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request

RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
FROM_EMAIL = 'Decision Catcher <noreply@neurocatchers.com>'


def send_email(to, subject, html, reply_to=None):
    print(f"[resend] send_email: to={to}", flush=True)
    print(f"[resend] key_present={bool(RESEND_API_KEY)}, key_len={len(RESEND_API_KEY)}", flush=True)
    print(f"[resend] has_requests={HAS_REQUESTS}", flush=True)

    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY not configured")

    payload = {
        'from': FROM_EMAIL,
        'to': [to] if isinstance(to, str) else to,
        'subject': subject,
        'html': html,
    }
    if reply_to:
        payload['reply_to'] = reply_to

    headers = {
        'Authorization': f'Bearer {RESEND_API_KEY}',
        'Content-Type': 'application/json',
    }

    try:
        if HAS_REQUESTS:
            resp = requests.post('https://api.resend.com/emails', json=payload, headers=headers, timeout=15)
            print(f"[resend] status={resp.status_code}, body={resp.text[:300]}", flush=True)
            if resp.status_code >= 400:
                raise RuntimeError(f"Resend {resp.status_code}: {resp.text}")
            return resp.json()
        else:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request('https://api.resend.com/emails', data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read().decode('utf-8')
                print(f"[resend] urllib body={body[:300]}", flush=True)
                return json.loads(body)
    except Exception as e:
        print(f"[resend] EXCEPTION {type(e).__name__}: {e}", flush=True)
        print(f"[resend] {traceback.format_exc()}", flush=True)
        raise


def parent_consent_email(parent_name, parent_email, child_name, child_age, consent_url, language='ko'):
    print(f"[resend] parent_consent_email: parent_email={parent_email}", flush=True)

    if language == 'ko':
        subject = f'[Decision Catcher] {child_name} 자녀의 베타 참여 동의 요청'
        html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:system-ui,sans-serif;background:#f0eee9;padding:40px 20px;color:#1a1a1a">
<div style="max-width:600px;margin:0 auto;background:#fff;border:2px solid #1a1a1a;border-radius:20px;padding:40px">
<div style="text-align:center;margin-bottom:30px">
<div style="display:inline-block;background:#C9444F;color:#fff;padding:6px 16px;border-radius:999px;font-size:13px;font-weight:700;margin-bottom:16px">CNA v7 베타</div>
<h1 style="font-size:26px;margin:0">Decision Catcher</h1>
<p style="color:#5a4a35;margin-top:8px">Boston Neuromind LLC</p>
</div>
<p>안녕하세요, <strong>{parent_name}</strong>님</p>
<p>자녀 <strong>{child_name}</strong> ({child_age}세)이(가) Boston Neuromind LLC의 <strong>Decision Catcher 베타 프로그램</strong> 참여를 신청했습니다.</p>
<p>자녀가 본인 Assent를 완료했으며, <strong>부모/법정 보호자의 동의</strong>가 필요합니다.</p>
<div style="background:#fff8e1;border-left:4px solid #f59e0b;padding:14px 18px;border-radius:8px;margin:24px 0">
<strong>📋 베타 참여 안내:</strong><br>
· 총 8주 (4-8주 프로토콜 + 4주 outcome)<br>
· 초기 평가 1회 (60-90분)<br>
· 주간 진행 상태 입력 (5-10분)<br>
· 최종 outcome 평가
</div>
<p>아래 링크로 동의서를 확인하고 서명해 주세요:</p>
<div style="text-align:center;margin:30px 0">
<a href="{consent_url}" style="display:inline-block;background:#C9444F;color:#fff;padding:14px 32px;border-radius:12px;text-decoration:none;font-weight:700;font-size:15px">동의서 확인 및 서명</a>
</div>
<p style="font-size:13px;color:#666;margin-top:24px">
· 본 링크는 7일간 유효합니다.<br>
· 언제든 자녀의 참여를 철회하실 수 있습니다.<br>
· 문의: support@neurocatchers.com
</p>
<hr style="border:none;border-top:1px solid #eee;margin:30px 0">
<p style="font-size:11px;color:#999;text-align:center">Boston Neuromind LLC · Canton, Massachusetts</p>
</div></body></html>"""
    else:
        subject = f'[Decision Catcher] Parental Consent Request — {child_name}'
        html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:system-ui,sans-serif;background:#f0eee9;padding:40px 20px;color:#1a1a1a">
<div style="max-width:600px;margin:0 auto;background:#fff;border:2px solid #1a1a1a;border-radius:20px;padding:40px">
<div style="text-align:center;margin-bottom:30px">
<div style="display:inline-block;background:#C9444F;color:#fff;padding:6px 16px;border-radius:999px;font-size:13px;font-weight:700;margin-bottom:16px">CNA v7 Beta</div>
<h1 style="font-size:26px;margin:0">Decision Catcher</h1>
<p style="color:#5a4a35;margin-top:8px">Boston Neuromind LLC</p>
</div>
<p>Dear <strong>{parent_name}</strong>,</p>
<p>Your child <strong>{child_name}</strong> (age {child_age}) has requested to participate in the <strong>Decision Catcher Beta Program</strong> by Boston Neuromind LLC.</p>
<p>Your child has completed their assent. <strong>Parental/legal guardian consent</strong> is required to proceed.</p>
<div style="background:#fff8e1;border-left:4px solid #f59e0b;padding:14px 18px;border-radius:8px;margin:24px 0">
<strong>📋 Beta Program Overview:</strong><br>
· Total 8 weeks (4-8 week protocol + 4-week outcome)<br>
· Initial assessment (60-90 minutes)<br>
· Weekly progress entries (5-10 minutes)<br>
· Final outcome assessment
</div>
<p>Please review and sign the consent form using the link below:</p>
<div style="text-align:center;margin:30px 0">
<a href="{consent_url}" style="display:inline-block;background:#C9444F;color:#fff;padding:14px 32px;border-radius:12px;text-decoration:none;font-weight:700;font-size:15px">Review & Sign Consent</a>
</div>
<p style="font-size:13px;color:#666;margin-top:24px">
· This link expires in 7 days.<br>
· You may withdraw your child at any time.<br>
· Contact: support@neurocatchers.com
</p>
<hr style="border:none;border-top:1px solid #eee;margin:30px 0">
<p style="font-size:11px;color:#999;text-align:center">Boston Neuromind LLC · Canton, Massachusetts</p>
</div></body></html>"""

    return send_email(parent_email, subject, html)
