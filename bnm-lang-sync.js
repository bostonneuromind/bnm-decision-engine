// bnm-lang-sync.js v6 — strict explicit lang sync (no defaults beyond config)
//   v5: also fills body[data-lang] on DOM-ready so a brand-new page needs only
//       <script src=".../bnm-lang-sync.js"> + <html lang> + ko-text/en-text markers.
//   v6: doc-only — clarify that each familyDomains entry auto-covers ALL of its
//       subdomains (*.d), so new subdomains need no config change.
// Decision tree:
//   URL ?lang=ko|en > localStorage[storageKey] > old-key migration > defaultLang
// Effect:
//   1. ALL <a> tags get ?lang=<current> appended (family domains + same domain .html)
//   2. On pages with -en.html/-ko.html variants, auto-redirect if URL explicit
//   3. bnmSetLang(ko|en) updates everything (localStorage, links, redirect if applicable)
//
// ┌───────────────────────────────────────────────────────────────────────────┐
// │  CONFIG — the only block a buyer / new deployment edits.                    │
// │  Override without editing this file by setting window.BNM_LANG_CONFIG = {…} │
// │  BEFORE this script loads (same keys; partial overrides are merged).        │
// │                                                                             │
// │  familyDomains : sites that share language across the group via ?lang=.     │
// │                  EACH ENTRY AUTO-COVERS ALL ITS SUBDOMAINS (*.d): listing    │
// │                  'neurocatchers.com' already matches track. / decision. /    │
// │                  learning. / adhd. / any-new.neurocatchers.com — no edit     │
// │                  needed for new subdomains. (Lookalikes like                 │
// │                  evil-neurocatchers.com are NOT matched — the dot prefix.)   │
// │                  Standalone site → keep just your own domain (or []).        │
// │                  A wrong/empty list never breaks the in-page toggle or       │
// │                  persistence — only cross-domain propagation is skipped.     │
// │  wwwCanonical  : EXACT apex hosts whose host→www redirect DROPS the query    │
// │                  string (external registrar/S3 forwarding). Links to these   │
// │                  exact hosts are sent straight to www.* so ?lang= survives.  │
// │                  Subdomains (track./decision./learning. on Vercel/CF) keep   │
// │                  the query natively, so they are NOT and need NOT be listed. │
// │  defaultLang   : last-resort language ('ko'|'en') when none stored / in URL.│
// │  storageKey    : localStorage key for the remembered language.              │
// │  oldKeys       : legacy keys migrated into storageKey (ko/en values only).  │
// └───────────────────────────────────────────────────────────────────────────┘
var BNM_LANG_CFG = (function () {
  var cfg = {
    familyDomains: [
      'bostonneuromind.com',
      'talkcatcher.com',
      'neurocatchers.com',
      'modalitycatcher.com'
    ],
    wwwCanonical: ['talkcatcher.com', 'modalitycatcher.com'],
    defaultLang: 'en',
    storageKey: 'bnm_lang',
    oldKeys: ['nc_lang', 'ncLang', 'tcm_lang', 'tc_lang', 'mc_lang_v', 'tc_docs_lang']
  };
  try {
    var o = (typeof window !== 'undefined') && window.BNM_LANG_CONFIG;
    if (o && typeof o === 'object') {
      if (Array.isArray(o.familyDomains)) cfg.familyDomains = o.familyDomains;
      if (Array.isArray(o.wwwCanonical)) cfg.wwwCanonical = o.wwwCanonical;
      if (o.defaultLang === 'ko' || o.defaultLang === 'en') cfg.defaultLang = o.defaultLang;
      if (typeof o.storageKey === 'string' && o.storageKey) cfg.storageKey = o.storageKey;
      if (Array.isArray(o.oldKeys)) cfg.oldKeys = o.oldKeys;
    }
  } catch (e) {}
  // Precompute a www-canonical lookup map (defensive against malformed arrays).
  cfg.wwwMap = {};
  try {
    for (var i = 0; i < cfg.wwwCanonical.length; i++) cfg.wwwMap[cfg.wwwCanonical[i]] = 1;
  } catch (e) { cfg.wwwMap = {}; }
  try { if (typeof window !== 'undefined') window.BNM_LANG_CFG = cfg; } catch (e) {}
  return cfg;
})();

(function() {
  var STORAGE_KEY = BNM_LANG_CFG.storageKey;
  var OLD_KEYS = BNM_LANG_CFG.oldKeys;
  var DEFAULT_LANG = BNM_LANG_CFG.defaultLang;

  function canonicalHost(h) { return BNM_LANG_CFG.wwwMap[h] ? ('www.' + h) : h; }

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
      if (urlLang === 'ko' || urlLang === 'en') {
        // explicit URL — also persist
        try { localStorage.setItem(STORAGE_KEY, urlLang); } catch(e) {}
        return urlLang;
      }
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
    return DEFAULT_LANG;
  }

  function isFamilyDomain(hostname) {
    var fam = BNM_LANG_CFG.familyDomains;
    for (var i = 0; i < fam.length; i++) {
      var d = fam[i];
      if (hostname === d || hostname.endsWith('.' + d)) return true;
    }
    return false;
  }

  // Add ?lang= to every anchor that points to .html or family domains
  function syncOutboundLinks(lang) {
    var anchors = document.querySelectorAll('a[href]');
    for (var i = 0; i < anchors.length; i++) {
      var a = anchors[i];
      try {
        var rawHref = a.getAttribute('href');
        // skip pure anchors, mailto, tel, javascript, etc.
        if (!rawHref) continue;
        if (rawHref.charAt(0) === '#') continue;
        if (rawHref.indexOf('mailto:') === 0) continue;
        if (rawHref.indexOf('tel:') === 0) continue;
        if (rawHref.indexOf('javascript:') === 0) continue;

        var url = new URL(a.href, location.href);
        // Cross-domain family
        if (isFamilyDomain(url.hostname) && url.hostname !== location.hostname) {
          url.hostname = canonicalHost(url.hostname);
          url.searchParams.set('lang', lang);
          a.href = url.toString();
          continue;
        }
        // Same-domain: .html pages OR root path
        if (url.hostname === location.hostname) {
          var p = url.pathname;
          if (p.endsWith('.html') || p === '/' || p === '') {
            url.searchParams.set('lang', lang);
            a.href = url.toString();
          }
        }
      } catch(e) {}
    }
  }

  // If URL has ?lang=en and current page has a -en variant available, switch
  function maybeRedirectVariant(lang, forceCheck) {
    var path = location.pathname;
    var newPath = null;

    if (lang === 'en') {
      if (path.endsWith('.html') && !path.endsWith('-en.html') && !path.endsWith('-ko.html')) {
        newPath = path.replace(/\.html$/, '-en.html');
      } else if (path.endsWith('-ko.html')) {
        newPath = path.replace(/-ko\.html$/, '-en.html');
      }
    } else if (lang === 'ko') {
      if (path.endsWith('-en.html')) {
        newPath = path.replace(/-en\.html$/, '.html');
      }
    }

    if (newPath && newPath !== path) {
      try {
        var xhr = new XMLHttpRequest();
        xhr.open('HEAD', newPath, true);
        xhr.onload = function() {
          if (xhr.status >= 200 && xhr.status < 400) {
            var params = new URLSearchParams(location.search);
            params.set('lang', lang);
            location.replace(newPath + '?' + params.toString() + location.hash);
          }
        };
        xhr.onerror = function() {};
        xhr.send();
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

  // Check if URL had explicit lang BEFORE we apply (for redirect decision)
  var urlHadExplicitLang = false;
  try {
    var u = new URLSearchParams(location.search).get('lang');
    urlHadExplicitLang = (u === 'ko' || u === 'en');
  } catch(e) {}

  var initial = detectLang();
  applyLang(initial);

  // Only redirect on initial load if URL explicitly said the lang
  // (avoids surprising visitors who landed via direct URL with no ?lang=)
  if (urlHadExplicitLang) {
    maybeRedirectVariant(initial, true);
  }

  window.bnmGetLang = function() { return window.BNM_LANG || DEFAULT_LANG; };
  window.bnmSetLang = function(newLang) {
    if (newLang !== 'ko' && newLang !== 'en') return;
    applyLang(newLang);
    if (typeof window.setLang === 'function' && window.setLang !== window.bnmSetLang) {
      try { window.setLang(newLang); } catch(e) {}
    }
    // Manual toggle - always try variant redirect
    maybeRedirectVariant(newLang, true);
  };

  // When the <head> script runs before <body>, applyLang() couldn't set
  // body[data-lang] yet. Set it on DOM-ready to the canonical language so any
  // static page that styles via body[data-lang] honors first-visit-en / ?lang= /
  // remembered choice with nothing but this one <script> tag — even legacy pages
  // whose own inline toggle defaulted to ko. body[data-lang] === current lang is
  // true by definition, and this runs after in-body inline scripts, so it's the
  // authoritative first-paint value (v6: set always, not only-if-unset).
  function fillBodyLang() {
    try {
      if (document.body) document.body.setAttribute('data-lang', window.BNM_LANG);
    } catch(e) {}
  }
  // Re-sync links + body[data-lang] after DOM ready (in case <head> script ran before <body>)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() { fillBodyLang(); syncOutboundLinks(window.BNM_LANG); });
  } else {
    fillBodyLang();
    syncOutboundLinks(window.BNM_LANG);
  }

  // Re-sync after dynamic content
  if (typeof MutationObserver !== 'undefined') {
    var debounceTimer = null;
    var setupObs = function() {
      if (!document.body) return;
      var obs = new MutationObserver(function() {
        if (debounceTimer) clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function() {
          syncOutboundLinks(window.BNM_LANG);
        }, 200);
      });
      obs.observe(document.body, { childList: true, subtree: true });
    };
    if (document.body) {
      setupObs();
    } else {
      document.addEventListener('DOMContentLoaded', setupObs);
    }
  }
})();

// Bonus: watch <html lang="..."> attribute changes (React sites often update this)
(function() {
  try {
    if (typeof MutationObserver === 'undefined') return;
    var html = document.documentElement;
    function isFamily(h) {
      var fam = BNM_LANG_CFG.familyDomains;
      for (var j = 0; j < fam.length; j++) {
        if (h === fam[j] || h.endsWith('.' + fam[j])) return true;
      }
      return false;
    }
    function canonicalHost(h) { return BNM_LANG_CFG.wwwMap[h] ? ('www.' + h) : h; }
    var attrObs = new MutationObserver(function(mutations) {
      for (var i = 0; i < mutations.length; i++) {
        var m = mutations[i];
        if (m.type === 'attributes' && m.attributeName === 'lang') {
          var newLang = html.getAttribute('lang');
          if ((newLang === 'ko' || newLang === 'en') && newLang !== window.BNM_LANG) {
            window.BNM_LANG = newLang;
            try { localStorage.setItem(BNM_LANG_CFG.storageKey, newLang); } catch(e) {}
            // Re-sync links
            var anchors = document.querySelectorAll('a[href]');
            for (var k = 0; k < anchors.length; k++) {
              var a = anchors[k];
              try {
                var rh = a.getAttribute('href');
                if (!rh || rh.charAt(0) === '#') continue;
                if (rh.indexOf('mailto:') === 0 || rh.indexOf('tel:') === 0 || rh.indexOf('javascript:') === 0) continue;
                var url = new URL(a.href, location.href);
                if (isFamily(url.hostname) && url.hostname !== location.hostname) {
                  url.hostname = canonicalHost(url.hostname);
                  url.searchParams.set('lang', newLang);
                  a.href = url.toString();
                } else if (url.hostname === location.hostname) {
                  var p = url.pathname;
                  if (p.endsWith('.html') || p === '/' || p === '') {
                    url.searchParams.set('lang', newLang);
                    a.href = url.toString();
                  }
                }
              } catch(e) {}
            }
          }
        }
      }
    });
    attrObs.observe(html, { attributes: true, attributeFilter: ['lang'] });
  } catch(e) {}
})();
