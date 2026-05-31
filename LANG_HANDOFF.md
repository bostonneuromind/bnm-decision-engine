# 영한(ko/en) 언어 시스템 — HANDOFF

전 사이트(neurocatchers / bostonneuromind / modalitycatcher / talkcatcher / learning / decision)는
**하나의 공용 스크립트 `bnm-lang-sync.js`**로 언어를 통일한다. 4 사이트 + 2 엔진에 **동일본(MD5 일치)**으로
배포한다 — 한 곳을 고치면 나머지에 복사한다.

## 4원칙 (반드시 유지)
1. **처음 접속 en** — 저장값·URL 없으면 영어.
2. **마지막 선택 기억** — 토글하면 `localStorage['bnm_lang']`에 저장.
3. **토글 후 지속** — 다시 바꾸기 전까지 유지(페이지/세션 넘어가도).
4. **도메인 왕복 유지** — 사이트 간 이동 시 `?lang=`로 현재 언어 전파.

## 동작 요약
- canonical 저장소: `localStorage['bnm_lang']` (`'ko'`|`'en'`).
- 우선순위: `URL ?lang=` > `bnm_lang` > 구키 마이그레이션 > `defaultLang`(en).
- 모든 `<a href>`(family 도메인 + 같은 도메인 .html)에 `?lang=<현재>` 자동부착(MutationObserver, React 렌더 링크 포함).
- `<html lang>` + `<body data-lang>` 자동 설정. `<html lang>` 변경(React)도 감지해 재동기화.
- 공개 API: `window.bnmGetLang()` → `'ko'|'en'`, `window.bnmSetLang('ko'|'en')` → 저장+적용+링크동기화.
- 마커: `class="ko-text"`/`class="en-text"` + CSS `body[data-lang="en"] .ko-text{display:none}` 식.

## 새 페이지 추가 — 이 한 줄이면 4원칙 자동 적용 (정적 HTML)
`<head>` **최상단**(다른 인라인 lang 스크립트보다 먼저)에:
```html
<html lang="en">
<head>
  <script src="/bnm-lang-sync.js"></script>   <!-- 서브디렉토리면 ../ 깊이 맞춰서 -->
  ...
</head>
```
콘텐츠 마커 + CSS:
```html
<style>
  .ko-text{display:none}.en-text{display:none}
  body[data-lang="ko"] .ko-text{display:inline}
  body[data-lang="en"] .en-text{display:inline}
</style>
<span class="ko-text">한국어</span><span class="en-text">English</span>
```
토글 버튼(있으면):
```html
<button onclick="window.bnmSetLang('ko')">한국어</button>
<button onclick="window.bnmSetLang('en')">EN</button>
```
> 정적 `<body data-lang="...">`는 **넣지 마라**(넣을 거면 `"en"`). 안 넣으면 스크립트가 DOM-ready에
> `bnm_lang` 값으로 채운다(v5). 기본값을 `ko`로 강제하는 자체 read-block은 만들지 마라.

## React / Next.js 페이지
- 스크립트 주입: Next.js는 `_app`에서 `<Script src="/bnm-lang-sync.js" strategy="beforeInteractive" />`.
- lang state 초기값: `window.bnmGetLang ? window.bnmGetLang() : 'en'`.
- 토글 시: 로컬 state + `if (window.bnmSetLang) window.bnmSetLang(next)` 동시 호출.
- 자체 `setItem`은 `bnm_lang` 키로만(다른 키 ❌). 기본값은 항상 `en`.

## CONFIG (판매/단독 분리 대비)
`bnm-lang-sync.js` 상단 `BNM_LANG_CFG` 블록 1개만 고치면 됨. 또는 스크립트 로드 전에
`window.BNM_LANG_CONFIG = {...}`로 오버라이드(부분 병합·잘못된 값 무시).
- `familyDomains`: 언어를 공유할 도메인들. **단독 사이트는 자기 도메인만(또는 [])** — 리스트가 비거나
  틀려도 내부 토글/지속은 무에러로 작동하고 cross-domain 전파만 조용히 스킵된다.
- `wwwCanonical`: **apex→www 301이 쿼리스트링을 떨구는** 도메인(현재 talkcatcher.com, modalitycatcher.com).
  이 도메인으로 가는 링크는 `www.*`로 직접 보내 `?lang=`·https를 보존한다. (근본은 apex DNS를 CF로
  돌리는 것이지만 외부 레지스트라 forwarding이라 보류 — `[[catcher-sites-deploy-url]]` 참고.)
- `defaultLang`/`storageKey`/`oldKeys`도 여기서.

## 빠진 섬(공용 미로드) 감지
새 페이지가 lang 마커/토글을 쓰는데 `bnm-lang-sync.js`를 안 실으면 4원칙이 안 붙는다. 점검:
```
node tools/check-lang.mjs .          # 현재 repo
node tools/check-lang.mjs ../talkcatcher
```
lang 마커/토글이 있는데 스크립트를 안 실은 .html을 출력한다.

## 라이브 검증
헤드리스(puppeteer-core + 설치 Chrome, BasicAuth admin:bnm1#, **www 호스트**로 — apex 서브패스는 404).
fresh→en / `?lang=ko`→ko / reload 지속 / 토글 / 도메인 왕복(`A?lang=ko`의 링크가 `www.B/?lang=ko`인지) 확인.
