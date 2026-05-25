// bnm-lang-sync.js v3 — strict explicit lang sync (no defaults)
// Decision tree:
//   URL ?lang=ko|en > localStorage 'bnm_lang' > 'ko' (last-resort default — Decision Engine is Korean-primary)
// Effect:
//   1. ALL <a> tags get ?lang=<current> appended (family domains + same domain .html)
//   2. On pages with -en.html/-ko.html variants, auto-redirect if URL explicit
//   3. bnmSetLang(ko|en) updates everything (localStorage, links, redirect if applicable)
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
    return 'ko'; // Decision Engine last-resort default (Korean-primary)
  }

  function isFamilyDomain(hostname) {
    for (var i = 0; i < FAMILY_DOMAINS.length; i++) {
      var d = FAMILY_DOMAINS[i];
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

  window.bnmGetLang = function() { return window.BNM_LANG || 'ko'; };
  window.bnmSetLang = function(newLang) {
    if (newLang !== 'ko' && newLang !== 'en') return;
    applyLang(newLang);
    if (typeof window.setLang === 'function' && window.setLang !== window.bnmSetLang) {
      try { window.setLang(newLang); } catch(e) {}
    }
    // Manual toggle - always try variant redirect
    maybeRedirectVariant(newLang, true);
  };

  // Re-sync links after DOM ready (in case <head> script ran before <body>)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() { syncOutboundLinks(window.BNM_LANG); });
  } else {
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
    var attrObs = new MutationObserver(function(mutations) {
      for (var i = 0; i < mutations.length; i++) {
        var m = mutations[i];
        if (m.type === 'attributes' && m.attributeName === 'lang') {
          var newLang = html.getAttribute('lang');
          if ((newLang === 'ko' || newLang === 'en') && newLang !== window.BNM_LANG) {
            window.BNM_LANG = newLang;
            try { localStorage.setItem('bnm_lang', newLang); } catch(e) {}
            // Re-sync links
            var anchors = document.querySelectorAll('a[href]');
            var FAMILY = ['bostonneuromind.com', 'talkcatcher.com', 'neurocatchers.com', 'modalitycatcher.com'];
            function isFamily(h) {
              for (var j = 0; j < FAMILY.length; j++) {
                if (h === FAMILY[j] || h.endsWith('.' + FAMILY[j])) return true;
              }
              return false;
            }
            for (var k = 0; k < anchors.length; k++) {
              var a = anchors[k];
              try {
                var rh = a.getAttribute('href');
                if (!rh || rh.charAt(0) === '#') continue;
                if (rh.indexOf('mailto:') === 0 || rh.indexOf('tel:') === 0 || rh.indexOf('javascript:') === 0) continue;
                var url = new URL(a.href, location.href);
                if (isFamily(url.hostname) && url.hostname !== location.hostname) {
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
