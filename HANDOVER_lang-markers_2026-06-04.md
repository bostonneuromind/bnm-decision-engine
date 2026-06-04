# HANDOVER — decision 분과 페이지 영한 토글 완성 (2026-06-04)

세션: 2026-06-04. chat Claude → 다음 인스턴스 인계.
**이 문서 먼저 읽을 것.** repo: `C:\Users\alice\Dev\bostonneuromind\bnm-decision-engine`
라이브: decision.neurocatchers.com (Vercel 자동배포)

---

## ⚡ 한 줄 상태
decision 4분과(attention/peak/learning-disability/learning-enhancement) × {index,diagnosis,training,needs} 16페이지의
EN 모드 한글 누락을 전부 해소했다. 토글 버튼·폰트·목차·다이어그램·eyebrow·sec-no 전부 ko/en 마커 완비. 전부 push됨.

---

## ✅ 이번 세션 완료 (전부 push, 되돌리지 말 것)

| 작업 | 범위 | commit |
|---|---|---|
| 토글 버튼 KO\|EN 세그먼트 통일 (`<span class="pill">` 두 버튼) | 12 division (index/diag/train ×4) | c8147e4·06b22fc·e4c10ec |
| 라벨 정규화 revert (할비 판단) | — | 57c442f |
| 버튼 간격 `.pill{margin-left:16px}` | 16 (needs 포함) | 113cb7a |
| 폰트 키움 (body 18.5→20px, .lead 21→22, .toc 15→16.5, .ev/.note/table 등) | 12 (index/diag/train ×4) | 33f36e2 |
| 목차(TOC) 영어 마커 (ko/en span) | 7 (LD/diagnosis는 기존 완료라 제외) | 33f36e2 |
| needs 제목(h1) 분과별 분화 (peak 유지) | 3 (attention/LD/LE) | 111c798 |
| attention/diagnosis References 중복 2블록→22개 합집합 병합 + 푸터 Peak→Attention | 1 | 4a0e824 |
| SVG 다이어그램 라벨 ko/en tspan + SVG 토글 CSS | 10 (peak/diag 먼저 ca608d5, 나머지 9 dabf9b7) | ca608d5·dabf9b7 |
| eyebrow + sec-no ko/en 마커 | 7 (LD/diagnosis 기존완료·index/needs 해당없음 제외) | (최신 commit) |

---

## 🩺 핵심 진단 (다음 사람 믿고 시작)

- **lang 엔진(bnm-lang-sync.js v6) 정상.** 기본 en. localStorage `bnm_lang` 우선. 첫 방문(시크릿)=영어.
- **마커 표준:** `<span class="ko-text">한글</span><span class="en-text">English</span>`. body[data-lang] CSS로 토글.
- **★ SVG 다이어그램은 `<tspan class="ko-text">…</tspan><tspan class="en-text">…</tspan>`** + 별도 CSS 규칙 필요:
  `tspan.en-text{display:none}tspan.ko-text{display:inline}body[data-lang=en] tspan.en-text{display:inline}body[data-lang=en] tspan.ko-text{display:none}`
  (일반 .en-text 규칙만으론 SVG tspan 토글 안 됨 — 이번에 추가함. 신규 SVG 만들 때 이 규칙 꼭 포함.)
- **검증 방법:** 시크릿 창(localStorage 깨끗) + `?v=숫자`(캐시 우회). EN 토글 시 본문·목차·다이어그램·eyebrow·sec-no 전부 영어 통일 확인.

---

## 🔴 남은 작업 (다음 세션)

1. **★ 라이브 전수 육안 검증** — 16페이지 시크릿 창 EN 토글로 한글 잔존 0 최종 확인. (코드·반영은 확인됨, 일부 페이지만 육안 봄.)
2. **check-lang 가드 강화 (재발 방지 — 꼭)**:
   - 현 가드(`tools/check-lang.mjs`)는 "lang-sync 스크립트 로드됐나"만 검사 → 마커 누락·`data-lang=ko` 하드코딩·자체 lang함수는 못 잡음.
   - ⚠ Vercel 배포를 막지 않음(빨간 X만). 진짜 차단하려면 Vercel 빌드 단계에 연결 필요.
   - 추가할 검사: (a) eyebrow/sec-no/TOC/SVG text에 ko-text/en-text 짝 없는 맨몸 한글 → fail (b) 자체 applyLang/curLang/toggleLang 정의 → fail (c) `<body data-lang="ko">` → fail
3. **"학습" 대표 메뉴 라우팅** — 홈(bostonneuromind) landings.jsx에서 "학습" 클릭 시 learning-disability/index로 감. 의도인지 선택화면 띄울지 할비 결정 필요. (풀다운 6항목 링크는 정상.)
4. needs 4페이지 폰트 — index/diag/train은 20px 명조로 키웠으나 needs는 다른 템플릿(산세리프 18px)이라 skip됨. 톤 통일 원하면 별도.

---

## 🛡️ 작업 규칙 (할비 원칙)
- **push는 할비 판단.** Claude Code가 `--dangerously-skip-permissions`(alex 단축키)로 돌아서 묻지 않고 push할 수 있음 — 이번 세션 2회 발생. commit까지만 주고 push 시점은 할비 검증 후.
- **SVG·대량 작업은 chat Claude가 작업본 만들어 ZIP으로** 전달 → 할비가 PowerShell로 repo 복사 → Claude Code 검증 → push. (Claude Code가 라이브 파일 행별 편집하다 깨뜨리는 것 방지.)
- **앵커(#s10b/#t7b 등) 절대 변경 금지** — 목차 링크↔본문 섹션 짝. 이름 바꾸면 점프 깨짐.
- 추측 금지. 한 번에 다 밀지 말고 표본(1페이지) 검증 후 확장.
- ZIP은 분과 폴더 구조 유지(attention/peak/...) → 이름충돌 0.
- 한글 파일명은 PowerShell Resolve-Path에서 깨짐 → foreach Copy-Item 또는 와일드카드로 우회.

---

## 🔧 작업 방식 메모 (이번 세션 교훈)
- Claude Code 화면이 긴 출력을 "+N lines"로 접음 → ctrl+o 펼치거나 파일 저장 후 chat에 업로드가 확실.
- grep `[가-힣]`이 가운뎃점(·, U+00B7)·en-dash(–)를 한글로 오탐 → "맨몸 한글" 카운트는 실제 내용 확인 필요.
- SVG/eyebrow는 이미 한+영 혼재한 경우 있음("Attention · 판별진단 Differential Diagnosis") → 번역이 아니라 ko/en 분리.

## 🔗 빠른 참조
- 라이브: decision.neurocatchers.com
- 분과 경로: /attention/ /peak/ /learning-disability/ /learning-enhancement/ 각 index·diagnosis·training·needs
- repo: C:\Users\alice\Dev\bostonneuromind\bnm-decision-engine
- 마커 표준 문서: repo 내 LANG_HANDOFF.md
