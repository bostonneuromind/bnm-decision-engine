# decision.neurocatchers.com 배포 가이드

**Decision Catcher · CNA v7.0 베타 사이트**  
**Boston Neuromind LLC · 2026**

---

## 구조

```
decision_site/
├── public/                     # 정적 페이지 9개
│   ├── index.html              # 홈
│   ├── clinician.html          # 새 환자 평가
│   ├── result.html             # 평가 결과 (5축 + DDE + Decomp + Sim)
│   ├── protocol.html           # 프로토콜 표시
│   ├── outcome.html            # 4주 outcome + Re-routing
│   ├── manual.html             # 매뉴얼 hub
│   ├── manual-ko.html          # 한국어 매뉴얼 (14장)
│   ├── manual-en.html          # English manual
│   ├── beta-guide.html         # 베타 운영 가이드
│   ├── style.css               # 공통 스타일
│   └── decision.js             # 공통 JS (인증, API 호출)
├── api/                        # Vercel serverless
│   ├── cna.py                  # 메인 핸들러
│   ├── cna_core/               # CNA v7 모듈 (복사)
│   └── config/                 # YAML
├── vercel.json                 # Vercel 배포 설정
├── requirements.txt            # Python 의존성
└── README.md
```

---

## 배포 옵션 3가지

### 옵션 A: Vercel (권장)

learning.neurocatchers.com과 동일 인프라.

```bash
npm i -g vercel
cd decision_site
vercel login
vercel --prod
```

Vercel dashboard에서 도메인 추가:
- Settings → Domains → Add `decision.neurocatchers.com`
- DNS 안내 따라 CNAME 추가:
  ```
  decision.neurocatchers.com  CNAME  cname.vercel-dns.com
  ```

확인 사항:
- Vercel Hobby: serverless 10초 timeout, 1024MB memory
- CNA v7 실행 약 2-3초 (cold start 시 +1초)
- 월 비용: $0 (Hobby) / $20 (Pro)

### 옵션 B: AWS S3 + CloudFront + Lambda

설정 시간 3-5시간, 월 ~$5.

### 옵션 C: Railway / Render

Python 네이티브 호스팅. 월 $5-10. Vercel보다 응답 빠름.

---

## DNS 설정

`decision.neurocatchers.com` subdomain:

```
Type    Name        Target
CNAME   decision    cname.vercel-dns.com         (Vercel)
CNAME   decision    d-xxxxx.cloudfront.net       (CloudFront)
```

Propagation 5-30분.

---

## 보안 단계

### Phase 1 (현재 베타): Password
- 모든 페이지에 `bnm1#` 비밀번호
- sessionStorage 인증

### Phase 2 (베타 종료 후): Supabase Auth
- 임상가 계정 생성
- HIPAA BAA 신청 (Supabase Pro $25/월)
- 환자별 RLS

### Phase 3 (정식): MFA
- TOTP 추가
- HIPAA full compliance

---

## Supabase 옵션

**옵션 1: learning 프로젝트 재사용** (권장)
- 같은 Supabase project (zatjbyeabxkfhmvopbtb)
- `cna_*` 테이블 16개 추가
- 비용 절감

**옵션 2: 새 프로젝트**
- $25/월 추가

테이블 생성:
```sql
\i /path/to/cna_v7/supabase/schema.sql
```

16개 테이블 생성 확인.

---

## 배포 후 확인

```bash
curl https://decision.neurocatchers.com/api/health

# Expected:
# {"status":"ok","version":"7.0.0","episode_count":0,"cna_available":true}
```

Full cycle 테스트:
```bash
curl -X POST https://decision.neurocatchers.com/api/full-cycle \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "TEST001",
    "cognitive_levels": {
      "sustained_attention": 7.8,
      "working_memory": 8.2,
      "emotional_regulation": 9.0,
      "time_awareness": 8.0,
      "self_awareness": 9.5
    },
    "symptom_vector": {"inattention": 0.85, "distractibility": 0.7},
    "biomarkers": {"hrv_rmssd": 32.0, "nback_accuracy": 0.65},
    "primary_clinical_axis": "attention",
    "motivation": 0.7,
    "temporal_history": {
      "onset_age": 8,
      "onset_category": "childhood",
      "course": "chronic",
      "duration_months": 240,
      "pervasiveness": "cross_setting",
      "stress_triggered": false
    }
  }'
```

결과 확인:
- `assessment.differential_diagnosis.primary_diagnosis == "adhd_inattentive"`
- `assessment.differential_diagnosis.comorbidity_pattern` 있음

---

## admin.html 갱신

기존 `neurocatchers.com/admin.html`에 6번째 카드 (D 빨강) 추가됨. 
갱신본 위치: `admin_update/admin.html`

작업:
1. 기존 파일 교체
2. 캐시 무효화 (Cache-Control)
3. 브라우저에서 6번째 카드 표시 확인

---

## 문의

bostonneuromind@gmail.com
