/* ============================================================================
 * service-admin.js — TrackCatcher 관리자 공유 로직 (11개 봇 공유)
 *   window.TCAdmin.init({ botKey, mount })  로 시작.
 *   기능: ① 무료 이용권(comp) 발급/목록/취소  ② 가입자 명단(20개 페이지)
 *         ③ 구독자 명단(20개 페이지)
 *   호출: comp-admin / users-admin Edge Function (관리자 JWT 필요).
 *   인증: window.TCAuth (tc-auth.js) — 관리자 3명 이메일 로그인.
 *   ⚠ 이 파일 하나만 고치면 11개 admin 전부 반영됨.
 * ========================================================================== */
(function () {
  const BASE = 'https://sepierapapsansprurpr.supabase.co/functions/v1';
  const COMP_ADMIN = BASE + '/comp-admin';
  const USERS_ADMIN = BASE + '/users-admin';
  const PER = 20;

  const isKo = () => document.body.dataset.lang === 'ko';
  const t = (ko, en) => (isKo() ? ko : en);
  const err = (m) => '<span style="color:#ff8a8a">' + m + '</span>';
  const ok = (m) => '<span style="color:#7ee0a0">' + m + '</span>';
  const emailRe = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

  async function call(url, bodyObj) {
    const s = await window.TCAuth.getSession();
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + ((s && s.access_token) || ''), 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyObj),
    });
    return { ok: res.ok, data: await res.json().catch(() => ({})) };
  }

  const BOT_OPTIONS = ['anxiety','sleep','burnout','ptsd','ocd','bipolar','autism','depression','learning','peak'];

  function shell(botKey) {
    // botKey 봇을 첫 옵션으로, 나머지는 ALL + 10개
    const others = BOT_OPTIONS.filter(b => b !== botKey);
    const botOpts = `<option value="${botKey}">${botKey} (this)</option>`
      + `<option value="">ALL bots</option>`
      + [botKey, ...others].filter((v,i,a)=>a.indexOf(v)===i && v!==botKey).map(b => `<option value="${b}">${b}</option>`).join('');
    return `
      <div class="ta-tabs">
        <button data-tab="comp" class="on">🎟️ ${t('무료 이용권','Free access')}</button>
        <button data-tab="users">👥 ${t('가입자','Users')}</button>
        <button data-tab="subs">💳 ${t('구독자','Subscribers')}</button>
      </div>
      <div class="ta-who" id="taWho"></div>

      <!-- COMP -->
      <div class="ta-pane" data-pane="comp">
        <div class="ta-field"><label>${t('이용자 이메일','User email')}</label><input id="taGEmail" type="email" placeholder="user@example.com"></div>
        <div class="ta-grid2">
          <div class="ta-field"><label>${t('대상 봇','Bot')}</label><select id="taGBot">${botOpts}</select></div>
          <div class="ta-field"><label>${t('기간','Period')}</label>
            <select id="taGPeriod">
              <option value="day">${t('1일','1 day')}</option>
              <option value="week">${t('1주일','1 week')}</option>
              <option value="month" selected>${t('1개월','1 month')}</option>
              <option value="year">${t('1년','1 year')}</option>
            </select></div>
        </div>
        <button class="ta-btn" id="taGrant">${t('이용권 발급 →','Grant access →')}</button>
        <div class="ta-note" id="taGMsg"></div>
        <div style="display:flex;align-items:center;justify-content:space-between;margin:16px 0 6px">
          <h3 class="ta-h3">${t('발급 내역','Granted access')}</h3>
          <button class="ta-btn ghost sm" id="taCompRefresh">${t('새로고침','Refresh')}</button>
        </div>
        <div id="taCompRows"></div>
      </div>

      <!-- USERS -->
      <div class="ta-pane" data-pane="users" style="display:none">
        <div class="ta-field"><label>${t('이메일 검색','Search email')}</label><input id="taUQ" type="text" placeholder="@example.com"></div>
        <div id="taUserRows"></div>
        <div class="ta-pager">
          <button class="ta-btn ghost sm" id="taUPrev">← ${t('이전','Prev')}</button>
          <span class="ta-pageno" id="taUPage">1</span>
          <button class="ta-btn ghost sm" id="taUNext">${t('다음','Next')} →</button>
        </div>
      </div>

      <!-- SUBS -->
      <div class="ta-pane" data-pane="subs" style="display:none">
        <div id="taSubRows"></div>
        <div class="ta-pager">
          <button class="ta-btn ghost sm" id="taSPrev">← ${t('이전','Prev')}</button>
          <span class="ta-pageno" id="taSPage">1</span>
          <button class="ta-btn ghost sm" id="taSNext">${t('다음','Next')} →</button>
        </div>
      </div>
    `;
  }

  function styles() {
    if (document.getElementById('ta-style')) return;
    const s = document.createElement('style');
    s.id = 'ta-style';
    s.textContent = `
      .ta-tabs{ display:flex; gap:6px; margin-bottom:16px; background:#f6f6f6; padding:4px; border-radius:10px; }
      .ta-tabs button{ flex:1; padding:9px; border:0; border-radius:7px; background:transparent; color:#6b6b6b; font-weight:700; font-size:15px; cursor:pointer; font-family:inherit; }
      .ta-tabs button.on{ background:var(--accent,#444); color:#ffffff; }
      .ta-who{ font-size:15px; color:#6b6b6b; margin-bottom:14px; }
      .ta-who b{ color:#1a1a1a; }
      .ta-field{ margin-bottom:13px; }
      .ta-field label{ display:block; font-size:15px; font-weight:700; color:#6b6b6b; margin-bottom:5px; }
      .ta-field input, .ta-field select{ width:100%; padding:12px 14px; border-radius:10px; border:1.5px solid #d8d8d8; background:#fafafa; color:#1a1a1a; font-family:inherit; font-size:15px; }
      .ta-field input:focus, .ta-field select:focus{ outline:none; border-color:var(--accent,#444); }
      .ta-field select option{ background:#ffffff; color:#1a1a1a; }
      .ta-grid2{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }
      .ta-btn{ width:100%; padding:14px; border:0; border-radius:11px; cursor:pointer; font-family:inherit; font-weight:800; font-size:16px; background:var(--accent,#444); color:#ffffff; transition:transform .12s; }
      .ta-btn:hover{ transform:translateY(-1px); }
      .ta-btn.ghost{ background:transparent; color:#1a1a1a; border:1.5px solid #d8d8d8; }
      .ta-btn.ghost:hover{ border-color:var(--accent,#444); }
      .ta-btn.sm{ width:auto; padding:8px 14px; font-size:15px; }
      .ta-note{ font-size:15px; color:#6b6b6b; text-align:center; margin-top:10px; line-height:1.5; }
      .ta-h3{ font-size:15px; font-weight:800; color:#1a1a1a; }
      .ta-row{ display:flex; align-items:center; gap:10px; padding:10px 12px; border:1px solid #d8d8d8; border-radius:10px; margin-bottom:8px; font-size:15px; background:#fafafa; }
      .ta-row .em{ flex:1; font-weight:700; color:#1a1a1a; word-break:break-all; }
      .ta-row .meta{ color:#6b6b6b; white-space:nowrap; font-size:15px; }
      .ta-row .rev{ background:transparent; border:1px solid #d8d8d8; color:#6b6b6b; border-radius:8px; padding:5px 10px; font-size:15px; font-weight:700; cursor:pointer; font-family:inherit; }
      .ta-row .rev:hover{ border-color:#ff8a8a; color:#ff8a8a; }
      .ta-pager{ display:flex; align-items:center; justify-content:center; gap:14px; margin-top:14px; }
      .ta-pageno{ font-size:15px; font-weight:800; color:#1a1a1a; min-width:24px; text-align:center; }
    `;
    document.head.appendChild(s);
  }

  // ── COMP ──
  async function grant(botKey, $) {
    const email = $('#taGEmail').value.trim().toLowerCase();
    const bot = $('#taGBot').value; // '' = 전봇
    const period = $('#taGPeriod').value;
    const msg = $('#taGMsg');
    if (!emailRe.test(email)) { msg.innerHTML = err(t('유효한 이메일을 입력하세요.', 'Enter a valid email.')); return; }
    const btn = $('#taGrant'); btn.disabled = true;
    const { ok: o, data } = await call(COMP_ADMIN, { action: 'grant', email, bot: bot || null, period });
    btn.disabled = false;
    if (o && data.ok) { msg.innerHTML = ok(t('발급 완료: ', 'Granted: ') + email); $('#taGEmail').value = ''; loadComp($); }
    else { msg.innerHTML = err((data && (data.error || data.reason)) || t('발급 실패', 'Grant failed')); }
  }

  async function loadComp($) {
    const box = $('#taCompRows');
    box.innerHTML = '<div class="ta-note" style="text-align:left">' + t('불러오는 중…', 'Loading…') + '</div>';
    const { ok: o, data } = await call(COMP_ADMIN, { action: 'list' });
    if (!o || !data.ok) { box.innerHTML = err(t('목록 로드 실패', 'Failed to load')); return; }
    const list = data.rows || [];
    if (!list.length) { box.innerHTML = '<div class="ta-note" style="text-align:left">' + t('발급 내역이 없습니다.', 'No grants yet.') + '</div>'; return; }
    box.innerHTML = '';
    list.forEach(r => {
      const until = new Date(r.expires_at);
      const expired = until.getTime() < Date.now();
      const el = document.createElement('div');
      el.className = 'ta-row';
      el.innerHTML = '<span class="em">' + r.email + '</span>'
        + '<span class="meta">' + (r.bot || 'ALL') + ' · ' + r.period + ' · ~' + until.toISOString().slice(0, 10) + (expired ? ' (exp)' : '') + '</span>'
        + '<button class="rev" data-id="' + r.id + '">' + t('취소', 'Revoke') + '</button>';
      el.querySelector('.rev').onclick = async (e) => {
        e.target.disabled = true;
        const { ok: ro } = await call(COMP_ADMIN, { action: 'revoke', id: e.target.getAttribute('data-id') });
        if (ro) loadComp($);
      };
      box.appendChild(el);
    });
  }

  // ── USERS (20/page) ──
  let uPage = 1, uQ = '';
  async function loadUsers($) {
    const box = $('#taUserRows');
    box.innerHTML = '<div class="ta-note" style="text-align:left">' + t('불러오는 중…', 'Loading…') + '</div>';
    const { ok: o, data } = await call(USERS_ADMIN, { action: 'list_users', page: uPage, perPage: PER, q: uQ });
    if (!o || !data.ok) { box.innerHTML = err((data && data.error) || t('로드 실패', 'Failed')); return; }
    const rows = data.rows || [];
    $('#taUPage').textContent = String(uPage);
    $('#taUPrev').disabled = uPage <= 1;
    $('#taUNext').disabled = !data.hasMore;
    if (!rows.length) { box.innerHTML = '<div class="ta-note" style="text-align:left">' + t('가입자가 없습니다.', 'No users.') + '</div>'; return; }
    box.innerHTML = '';
    rows.forEach(u => {
      const access = u.comps.length ? 'comp' : (u.subs.find(s => ['trialing','active'].includes(s.status)) ? 'sub' : '—');
      const el = document.createElement('div');
      el.className = 'ta-row';
      el.innerHTML = '<span class="em">' + (u.email || '(no email)') + '</span>'
        + '<span class="meta">' + (u.confirmed ? '✓' : '✗') + ' · ' + (u.created_at ? u.created_at.slice(0, 10) : '') + ' · ' + access + '</span>';
      box.appendChild(el);
    });
  }

  // ── SUBS (20/page) ──
  let sPage = 1;
  async function loadSubs($) {
    const box = $('#taSubRows');
    box.innerHTML = '<div class="ta-note" style="text-align:left">' + t('불러오는 중…', 'Loading…') + '</div>';
    const { ok: o, data } = await call(USERS_ADMIN, { action: 'list_subs', page: sPage, perPage: PER });
    if (!o || !data.ok) { box.innerHTML = err((data && data.error) || t('로드 실패', 'Failed')); return; }
    const rows = data.rows || [];
    $('#taSPage').textContent = String(sPage);
    $('#taSPrev').disabled = sPage <= 1;
    $('#taSNext').disabled = !data.hasMore;
    if (!rows.length) { box.innerHTML = '<div class="ta-note" style="text-align:left">' + t('구독자가 없습니다.', 'No subscribers.') + '</div>'; return; }
    box.innerHTML = '';
    rows.forEach(s => {
      const until = s.current_period_end || s.trial_ends_at;
      const el = document.createElement('div');
      el.className = 'ta-row';
      el.innerHTML = '<span class="em">' + s.bot + '</span>'
        + '<span class="meta">' + s.status + (until ? ' · ~' + String(until).slice(0, 10) : '') + '</span>';
      box.appendChild(el);
    });
  }

  function wire(botKey, root) {
    const $ = (sel) => root.querySelector(sel);
    // 탭 전환
    root.querySelectorAll('.ta-tabs button').forEach(b => {
      b.onclick = () => {
        root.querySelectorAll('.ta-tabs button').forEach(x => x.classList.remove('on'));
        b.classList.add('on');
        const tab = b.getAttribute('data-tab');
        root.querySelectorAll('.ta-pane').forEach(p => p.style.display = (p.getAttribute('data-pane') === tab) ? 'block' : 'none');
        if (tab === 'users') loadUsers($);
        if (tab === 'subs') loadSubs($);
      };
    });
    // comp
    $('#taGrant').onclick = () => grant(botKey, $);
    $('#taCompRefresh').onclick = () => loadComp($);
    // users
    let uTimer = null;
    $('#taUQ').addEventListener('input', () => { clearTimeout(uTimer); uTimer = setTimeout(() => { uQ = $('#taUQ').value.trim().toLowerCase(); uPage = 1; loadUsers($); }, 300); });
    $('#taUPrev').onclick = () => { if (uPage > 1) { uPage--; loadUsers($); } };
    $('#taUNext').onclick = () => { uPage++; loadUsers($); };
    // subs
    $('#taSPrev').onclick = () => { if (sPage > 1) { sPage--; loadSubs($); } };
    $('#taSNext').onclick = () => { sPage++; loadSubs($); };
    loadComp($);
  }

  // 공개 API
  window.TCAdmin = {
    // mount = comp 발급 등이 들어갈 컨테이너 element. botKey = 'adhd' 등.
    async init({ botKey, mount }) {
      styles();
      const render = async () => {
        let u = null;
        try { u = (window.TCAuth && TCAuth.configured()) ? await TCAuth.getUser() : null; } catch (e) { u = null; }
        if (u && TCAuth.isVerified(u)) {
          mount.innerHTML = shell(botKey);
          mount.querySelector('#taWho').innerHTML = (isKo() ? '관리자: ' : 'Admin: ') + '<b>' + u.email + '</b>';
          wire(botKey, mount);
        } else {
          mount.innerHTML = loginShell();
          mount.querySelector('#taLoginBtn').onclick = async () => {
            const email = mount.querySelector('#taAEmail').value.trim().toLowerCase();
            const pw = mount.querySelector('#taAPw').value;
            const msg = mount.querySelector('#taAMsg');
            if (!email || !pw) { msg.innerHTML = err(t('이메일·비밀번호 입력', 'Enter email and password')); return; }
            if (!window.TCAuth || !TCAuth.configured()) { msg.innerHTML = err(t('인증 미설정', 'Auth not configured')); return; }
            const { error } = await TCAuth.signIn({ email, password: pw });
            if (error) { msg.innerHTML = err(t('로그인 실패 (관리자 이메일 확인)', 'Login failed (check admin email)')); return; }
            render();
          };
          mount.querySelector('#taAPw').addEventListener('keypress', e => { if (e.key === 'Enter') mount.querySelector('#taLoginBtn').click(); });
        }
      };
      function loginShell() {
        styles();
        return `
          <div class="ta-note" style="text-align:left;margin:0 0 12px">${t('발급·조회하려면 관리자 이메일로 로그인하세요.', 'Log in with an admin email to manage.')}</div>
          <div class="ta-field"><label>Admin email</label><input id="taAEmail" type="email" placeholder="bostonneuromind@gmail.com"></div>
          <div class="ta-field"><label>${t('비밀번호', 'Password')}</label><input id="taAPw" type="password" placeholder="••••••••"></div>
          <button class="ta-btn" id="taLoginBtn">${t('관리자 로그인 →', 'Admin log in →')}</button>
          <div class="ta-note" id="taAMsg"></div>`;
      }
      await render();
    }
  };
})();
