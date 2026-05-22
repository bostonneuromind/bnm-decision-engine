// bnm-lang-sync.js v2 — 통합 동기화 + auto-redirect for -en/-ko file pairs
// localStorage key: bnm_lang
// URL query: ?lang=ko|en  (cross-domain sync)
// Auto-redirect: if URL has ?lang=en and -en variant exists, switch to it
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
    try {
      var urlLang = new URLSearchParams(location.search).get('lang');
      if (urlLang === 'ko' || urlLang === 'en') return urlLang;
    } catch(e) {}
    try {
      var saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'ko' || saved === 'en') return saved;
    } catch(e) {}
    var old = readOldKey();
    if (old) {
      try { localStorage.setItem(STORAGE_KEY, old); } catch(e) {}
      return old;
    }
    return 'en';
  }

  function isFamilyDomain(hostname) {
    for (var i = 0; i < FAMILY_DOMAINS.length; i++) {
      var d = FAMILY_DOMAINS[i];
      if (hostname === d || hostname.endsWith('.' + d)) return true;
    }
    return false;
  }

  // Auto-redirect: if lang=en and file has -ko/-en variant pair, switch URL
  // Pattern: 'foo.html' <-> 'foo-en.html', or 'foo-ko.html' <-> 'foo-en.html'
  function maybeRedirectVariant(lang) {
    var path = location.pathname;
    var newPath = null;

    if (lang === 'en') {
      // foo.html -> foo-en.html (if not already -en or -ko)
      if (path.endsWith('.html') && !path.endsWith('-en.html') && !path.endsWith('-ko.html')) {
        newPath = path.replace(/\.html$/, '-en.html');
      } else if (path.endsWith('-ko.html')) {
        newPath = path.replace(/-ko\.html$/, '-en.html');
      }
    } else if (lang === 'ko') {
      // foo-en.html -> foo.html (or foo-ko.html, prefer plain)
      if (path.endsWith('-en.html')) {
        newPath = path.replace(/-en\.html$/, '.html');
      }
    }

    if (newPath && newPath !== path) {
      // HEAD probe to check existence before redirecting (prevents 404 loop)
      var probeUrl = newPath + location.search;
      try {
        var xhr = new XMLHttpRequest();
        xhr.open('HEAD', newPath, true);
        xhr.onload = function() {
          if (xhr.status >= 200 && xhr.status < 400) {
            // Variant exists - redirect
            var qs = location.search;
            // Make sure lang param is preserved/set
            var params = new URLSearchParams(qs);
            params.set('lang', lang);
            location.replace(newPath + '?' + params.toString() + location.hash);
          }
          // else: variant doesn't exist, stay on current page
        };
        xhr.onerror = function() {};
        xhr.send();
      } catch(e) {}
    }
  }

  function syncOutboundLinks(lang) {
    var anchors = document.querySelectorAll('a[href]');
    for (var i = 0; i < anchors.length; i++) {
      var a = anchors[i];
      try {
        var url = new URL(a.href, location.href);
        // Cross-domain (family) — add ?lang=
        if (isFamilyDomain(url.hostname) && url.hostname !== location.hostname) {
          url.searchParams.set('lang', lang);
          a.href = url.toString();
          continue;
        }
        // Same-domain — also add ?lang= to preserve through navigation
        if (url.hostname === location.hostname && url.pathname.endsWith('.html')) {
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

  // Only redirect if explicit URL query said so (not localStorage-only),
  // to avoid surprising existing visitors.
  var explicitFromURL = false;
  try {
    var u = new URLSearchParams(location.search).get('lang');
    explicitFromURL = (u === 'ko' || u === 'en');
  } catch(e) {}

  applyLang(initial);

  // If URL explicitly requested a lang AND a matching variant file exists, redirect.
  if (explicitFromURL) {
    maybeRedirectVariant(initial);
  }

  window.bnmGetLang = function() { return window.BNM_LANG || 'en'; };
  window.bnmSetLang = function(newLang) {
    if (newLang !== 'ko' && newLang !== 'en') return;
    applyLang(newLang);
    if (typeof window.setLang === 'function' && window.setLang !== window.bnmSetLang) {
      try { window.setLang(newLang); } catch(e) {}
    }
    // Manual toggle - also try variant redirect
    maybeRedirectVariant(newLang);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() { syncOutboundLinks(window.BNM_LANG); });
  }

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
