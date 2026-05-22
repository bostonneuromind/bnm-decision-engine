// bnm-lang-sync.js — 통합 동기화 (Boston Neuromind family sites)
// localStorage key: bnm_lang
// URL query: ?lang=ko|en  (cross-domain sync)
// Old keys auto-migrated: nc_lang, ncLang, tcm_lang, tc_lang, mc_lang_v, tc_docs_lang
(function() {
  var STORAGE_KEY = 'bnm_lang';
  var OLD_KEYS = ['nc_lang', 'ncLang', 'tcm_lang', 'tc_lang', 'mc_lang_v', 'tc_docs_lang'];
  var FAMILY_DOMAINS = [
    'bostonneuromind.com',
    'talkcatcher.com',
    'neurocatchers.com',
    'modalitycatcher.com'
  ];

  function readOldKey() {
    for (var i = 0; i < OLD_KEYS.length; i++) {
      try {
        var v = localStorage.getItem(OLD_KEYS[i]);
        if (v === 'ko' || v === 'en') return v;
      } catch(e) {}
    }
    return null;
  }

  function detectLang() {
    // 1. URL query wins (cross-domain handoff)
    try {
      var urlLang = new URLSearchParams(location.search).get('lang');
      if (urlLang === 'ko' || urlLang === 'en') return urlLang;
    } catch(e) {}

    // 2. New unified key
    try {
      var saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'ko' || saved === 'en') return saved;
    } catch(e) {}

    // 3. Old key fallback (auto-migrate)
    var old = readOldKey();
    if (old) {
      try { localStorage.setItem(STORAGE_KEY, old); } catch(e) {}
      return old;
    }

    // 4. Default
    return 'en';
  }

  function isFamilyDomain(hostname) {
    for (var i = 0; i < FAMILY_DOMAINS.length; i++) {
      var d = FAMILY_DOMAINS[i];
      if (hostname === d || hostname.endsWith('.' + d)) return true;
    }
    return false;
  }

  function syncOutboundLinks(lang) {
    var anchors = document.querySelectorAll('a[href]');
    for (var i = 0; i < anchors.length; i++) {
      var a = anchors[i];
      try {
        var url = new URL(a.href, location.href);
        if (isFamilyDomain(url.hostname) && url.hostname !== location.hostname) {
          url.searchParams.set('lang', lang);
          a.href = url.toString();
        }
      } catch(e) {}
    }
  }

  function applyLang(lang) {
    window.BNM_LANG = lang;
    try { document.documentElement.setAttribute('lang', lang); } catch(e) {}
    try { if (document.body) document.body.setAttribute('data-lang', lang); } catch(e) {}
    try { localStorage.setItem(STORAGE_KEY, lang); } catch(e) {}
    syncOutboundLinks(lang);
    try {
      window.dispatchEvent(new CustomEvent('bnm-lang-change', { detail: { lang: lang } }));
    } catch(e) {}
  }

  var initial = detectLang();
  applyLang(initial);

  window.bnmGetLang = function() { return window.BNM_LANG || 'en'; };
  window.bnmSetLang = function(newLang) {
    if (newLang !== 'ko' && newLang !== 'en') return;
    applyLang(newLang);
    // If site has its own setLang (different from ours), call it to update UI
    if (typeof window.setLang === 'function' && window.setLang !== window.bnmSetLang) {
      try { window.setLang(newLang); } catch(e) {}
    }
  };

  // Re-sync links after DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() { syncOutboundLinks(window.BNM_LANG); });
  }

  // Re-sync after dynamic content (mutation observer, lightweight)
  if (typeof MutationObserver !== 'undefined') {
    var debounceTimer = null;
    var obs = new MutationObserver(function() {
      if (debounceTimer) clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function() {
        syncOutboundLinks(window.BNM_LANG);
      }, 300);
    });
    if (document.body) {
      obs.observe(document.body, { childList: true, subtree: true });
    } else {
      document.addEventListener('DOMContentLoaded', function() {
        obs.observe(document.body, { childList: true, subtree: true });
      });
    }
  }
})();
