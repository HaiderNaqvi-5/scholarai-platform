import os
import base64
import json
from typing import Any

import httpx


def decode_payload(token: str) -> dict[str, Any]:
    payload = token.split('.')[1]
    padding = '=' * (-len(payload) % 4)
    data = base64.urlsafe_b64decode(payload + padding)
    return json.loads(data)


base_url = os.getenv("SCHOLARAI_API_BASE_URL", "http://127.0.0.1:8000")

result: dict[str, Any] = {"base_url": base_url}
with httpx.Client(base_url=base_url, timeout=20.0) as client:
    health = client.get('/health')
    result['health_status'] = health.status_code
    result['health_body'] = health.json()

    s_login = client.post('/api/v1/auth/login', json={'email': 'student@example.com', 'password': 'strongpass1'})
    result['student_login_status'] = s_login.status_code
    s_body = s_login.json()
    s_claims: dict[str, Any] = decode_payload(s_body['access_token']) if s_login.status_code == 200 else {}
    result['student_claims'] = {
        'role': s_claims.get('role'),
        'policy_version': s_claims.get('policy_version'),
        'institution_scope': s_claims.get('institution_scope'),
        'capabilities_count': len(s_claims.get('capabilities', [])) if isinstance(s_claims.get('capabilities'), list) else None,
    }

    s_me = client.get('/api/v1/auth/me', headers={'Authorization': f"Bearer {s_body['access_token']}"}) if s_login.status_code == 200 else None
    result['student_me_status'] = s_me.status_code if s_me else None

    a_login = client.post('/api/v1/auth/login', json={'email': 'admin@example.com', 'password': 'strongpass1'})
    result['admin_login_status'] = a_login.status_code
    a_body = a_login.json()
    a_claims: dict[str, Any] = decode_payload(a_body['access_token']) if a_login.status_code == 200 else {}
    result['admin_claims'] = {
        'role': a_claims.get('role'),
        'policy_version': a_claims.get('policy_version'),
        'institution_scope': a_claims.get('institution_scope'),
        'capabilities_count': len(a_claims.get('capabilities', [])) if isinstance(a_claims.get('capabilities'), list) else None,
    }

    admin_curation = client.get('/api/v1/curation/records', headers={'Authorization': f"Bearer {a_body['access_token']}"}) if a_login.status_code == 200 else None
    student_curation = client.get('/api/v1/curation/records', headers={'Authorization': f"Bearer {s_body['access_token']}"}) if s_login.status_code == 200 else None
    result['admin_curation_status'] = admin_curation.status_code if admin_curation else None
    result['student_curation_status'] = student_curation.status_code if student_curation else None
    if admin_curation is not None:
        result['admin_curation_error'] = admin_curation.json() if admin_curation.status_code >= 400 else None
    if student_curation is not None:
        result['student_curation_error'] = student_curation.json() if student_curation.status_code >= 400 else None

print(json.dumps(result, indent=2))
