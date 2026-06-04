// ============================================================================
// tc-auth.js — TalkCatcher 인증 (Supabase Auth, 클라이언트)
// 의존: @supabase/supabase-js@2 (window.supabase) — index.html에서 먼저 로드.
// 노출: window.TCAuth
//
// 패턴 출처: bnm-learning-engine (api/src/routes/auth.js) — signUp /
//   signInWithPassword / signOut / getUser. 여기선 백엔드 서버 없이
//   브라우저에서 직접 Supabase Auth 사용(learning web/ 프론트와 동일 방식).
//
// ✅ [결정 확정 — 할비] talkcatcher 계정 = 신규 talkcatcher 전용 프로젝트.
//   sepierapapsansprurpr (별도 프로젝트, learning/phtz·symptom/zatj와 분리).
//   JWT 확인됨: ref=sepierapapsansprurpr, role=anon.
//   → learning 베타 auth 풀과 분리되어 talkcatcher 가입자가 섞이지 않음.
//   백업/RLS/tier 실태는 콘솔에서 할비가 확인(코드 밖).
//
//   (히스토리: phtz(learning Pro 공유) 추천 → 할비가 전용 프로젝트로 분리 결정.)
//
// ⚠️ 대시보드 설정(이메일 확인 ON/OFF, redirect URL allowlist, SMTP)은
//   코드 밖이라 여기서 보장 불가 — Supabase 콘솔에서 확인 필요.
// ============================================================================
(function () {
  'use strict';

  const TC_SUPABASE = {
    url: 'https://sepierapapsansprurpr.supabase.co',
    anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNlcGllcmFwYXBzYW5zcHJ1cnByIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODAyNTkxMDksImV4cCI6MjA5NTgzNTEwOX0.U1dPGHz7g1TjwFS56GVdPjzbzH6Ryc87C28YM9GP1z8',
  };

  let _client = null;

  function configured() {
    return !!(TC_SUPABASE.url && TC_SUPABASE.anonKey && window.supabase && window.supabase.createClient);
  }
  function client() {
    if (!configured()) return null;
    if (!_client) _client = window.supabase.createClient(TC_SUPABASE.url, TC_SUPABASE.anonKey);
    return _client;
  }
  function redirectTo() {
    try { return (window.location.origin || '') + '/'; } catch (e) { return '/'; }
  }
  const NOT_CONFIGURED = { error: { message: 'NOT_CONFIGURED' } };

  async function signUp({ name, email, password, lang }) {
    const c = client(); if (!c) return NOT_CONFIGURED;
    return await c.auth.signUp({
      email: email, password: password,
      options: {
        data: { display_name: name || '', language: lang || 'en' },
        emailRedirectTo: redirectTo(),
      },
    });
  }
  async function signIn({ email, password }) {
    const c = client(); if (!c) return NOT_CONFIGURED;
    return await c.auth.signInWithPassword({ email: email, password: password });
  }
  async function signOut() { const c = client(); if (c) { try { await c.auth.signOut(); } catch (e) {} } }
  async function resetPassword(email) {
    const c = client(); if (!c) return NOT_CONFIGURED;
    return await c.auth.resetPasswordForEmail(email, { redirectTo: redirectTo() });
  }
  async function updatePassword(password) {
    const c = client(); if (!c) return NOT_CONFIGURED;
    return await c.auth.updateUser({ password: password });
  }
  async function resendVerification(email) {
    const c = client(); if (!c) return NOT_CONFIGURED;
    try { return await c.auth.resend({ type: 'signup', email: email, options: { emailRedirectTo: redirectTo() } }); }
    catch (e) { return { error: { message: String(e && e.message || e) } }; }
  }
  async function getUser() {
    const c = client(); if (!c) return null;
    try { const { data } = await c.auth.getUser(); return data ? data.user : null; } catch (e) { return null; }
  }
  async function getSession() {
    const c = client(); if (!c) return null;
    try { const { data } = await c.auth.getSession(); return data ? data.session : null; } catch (e) { return null; }
  }
  function onChange(cb) {
    const c = client(); if (!c) return;
    try { c.auth.onAuthStateChange((event, session) => cb(event, session)); } catch (e) {}
  }
  function isVerified(user) { return !!(user && (user.email_confirmed_at || user.confirmed_at)); }

  window.TCAuth = {
    configured: configured, client: client,
    signUp: signUp, signIn: signIn, signOut: signOut,
    resetPassword: resetPassword, updatePassword: updatePassword, resendVerification: resendVerification,
    getUser: getUser, getSession: getSession, onChange: onChange, isVerified: isVerified,
    project: TC_SUPABASE.url,
  };
})();
