import io
p = 'api/self_sign.py'
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """                try:
                    parent_consent_email(
                        parent_email=row.get('parent_email'),
                        parent_name=row.get('parent_name'),
                        child_name=row.get('full_name'),
                        child_age=row.get('age'),
                        consent_token=token,
                        language=row.get('language', 'ko'),
                    )
                    print(f"parent consent email sent to {row.get('parent_email')}")
                except Exception as email_err:
                    print(f"email send failed: {email_err}")"""

new = """                try:
                    site_url = os.environ.get('SITE_URL', 'https://decision.neurocatchers.com')
                    consent_url = f"{site_url}/parent-consent.html?token={token}"
                    parent_consent_email(
                        parent_name=row.get('parent_name'),
                        parent_email=row.get('parent_email'),
                        child_name=row.get('full_name'),
                        child_age=row.get('age'),
                        consent_url=consent_url,
                        language=row.get('language', 'ko'),
                    )
                    print(f"parent consent email sent to {row.get('parent_email')}")
                except Exception as email_err:
                    print(f"email send failed: {email_err}")"""

if old in s:
    s = s.replace(old, new)
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)
    print('done')
else:
    print('OLD NOT FOUND - showing current call:')
    idx = s.find('parent_consent_email(')
    print(s[idx:idx+400])
