// SPA runtime for eliminate-jobs.
//
// A single-source side menu plus a client-side router. Every page (the four
// root sections and each pandoc-generated detail page under /arguments/) loads
// this script; it renders an identical menu and, on in-site navigation, swaps
// only <main> instead of doing a full page reload. Deep links / refresh still
// work because each real .html file is a self-contained shell that boots the
// same runtime.
(function () {
  'use strict';

  // ---- Single source of truth for the side menu (identical on every page). ----
  var MENU = [
    { id: 'index.html', label: 'Introduction' },
    { id: 'professions.html', label: 'All Professions' },
    { id: 'groups.html', label: 'Major Groups' },
    { id: 'consequences.html', label: 'Consequences' }
  ];

  // Per-view script dependencies (loaded once, lazily) and the EJTables init to
  // run after the view is mounted. Detail pages are detected by filename.
  var VIEWS = {
    'index':             { scripts: [], init: null },
    'professions':       { scripts: ['professions.js', 'tables.js'], init: 'professions' },
    'groups':            { scripts: ['groups.js', 'tables.js'], init: 'groups' },
    'consequences':      { scripts: [], init: null },
    'profession-detail': { scripts: [], init: null },
    'group-detail':      { scripts: ['professions.js', 'tables.js'], init: 'groupDetail' }
  };

  // Absolute base (directory of app.js) so dynamically loaded scripts and menu
  // links resolve correctly from any page depth, including the GH Pages subpath.
  var APP_BASE = (function () {
    var s = document.currentScript;
    if (s && s.src) return s.src.replace(/[^/]*$/, '');
    var m = document.querySelector('script[src$="app.js"]');
    if (m && m.src) return m.src.replace(/[^/]*$/, '');
    return '';
  })();

  var loaded = {};

  function loadScript(src) {
    if (loaded[src]) return Promise.resolve();
    if (document.querySelector('script[src="' + src + '"]')) {
      loaded[src] = true;
      return Promise.resolve();
    }
    return new Promise(function (resolve) {
      var s = document.createElement('script');
      s.src = src;
      s.onload = function () { loaded[src] = true; resolve(); };
      s.onerror = function () { resolve(); };
      document.body.appendChild(s);
    });
  }

  function ensureScripts(list) {
    var p = Promise.resolve();
    (list || []).forEach(function (rel) {
      p = p.then(function () { return loadScript(APP_BASE + rel); });
    });
    return p;
  }

  function fileName(path) {
    return path.split('/').pop().split('?')[0];
  }

  // Classify a path into a view kind. Group detail = pure digits (43.html);
  // profession detail contains a dash (15-1252.00.html).
  function viewKind(path) {
    var name = fileName(path);
    if (name === '' || name === 'index.html') return 'index';
    if (name === 'professions.html') return 'professions';
    if (name === 'groups.html') return 'groups';
    if (name === 'consequences.html') return 'consequences';
    if (/^\d+-/.test(name)) return 'profession-detail';
    if (/^\d+\.html$/.test(name)) return 'group-detail';
    return 'index';
  }

  // Which top-level menu section a path belongs to (for the active state).
  function sectionOf(path) {
    var k = viewKind(path);
    if (k === 'professions' || k === 'profession-detail') return 'professions.html';
    if (k === 'groups' || k === 'group-detail') return 'groups.html';
    if (k === 'consequences') return 'consequences.html';
    return 'index.html';
  }

  function renderMenu() {
    var nav = document.getElementById('side-menu');
    if (!nav) return;
    var active = sectionOf(location.pathname);
    var ul = document.createElement('ul');
    MENU.forEach(function (item) {
      var li = document.createElement('li');
      var a = document.createElement('a');
      a.href = APP_BASE + item.id;
      a.textContent = item.label;
      if (item.id === active) a.className = 'active';
      li.appendChild(a);
      ul.appendChild(li);
    });
    nav.innerHTML = '';
    nav.appendChild(ul);
  }

  // Replace the current view's content in <main id="app">, carrying over the
  // source page's className (e.g. "doc" for detail pages) so styles apply.
  function swapMain(doc) {
    var src = doc.querySelector('main');
    var app = document.getElementById('app') || document.querySelector('main');
    if (!src || !app) return;
    app.innerHTML = src.innerHTML;
    app.className = src.className || '';
  }

  function runInit(kind) {
    var v = VIEWS[kind];
    if (v && v.init && window.EJTables && typeof window.EJTables[v.init] === 'function') {
      window.EJTables[v.init]();
    }
  }

  function navigate(url, push) {
    var kind = viewKind(new URL(url, location.href).pathname);
    fetch(url).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.text();
    }).then(function (html) {
      var doc = new DOMParser().parseFromString(html, 'text/html');
      swapMain(doc);
      if (doc.title) document.title = doc.title;
      if (push) {
        try { history.pushState({ url: url }, '', url); } catch (e) { /* file:// */ }
      }
      renderMenu();
      window.scrollTo(0, 0);
      return ensureScripts(VIEWS[kind].scripts).then(function () { runInit(kind); });
    }).catch(function () {
      // Fallback to a full navigation (e.g. fetch failed).
      location.href = url;
    });
  }

  // Intercept in-site link clicks (anything under APP_BASE on this origin) so we
  // swap <main> instead of doing a full page load. External links (Wikipedia,
  // O*NET, etc.), target=_blank, #hash, and mailto: are left alone.
  document.addEventListener('click', function (e) {
    if (e.defaultPrevented || e.button !== 0) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest ? e.target.closest('a') : null;
    if (!a) return;
    if (a.target === '_blank' || a.hasAttribute('download')) return;
    var href = a.getAttribute('href');
    if (!href || href.charAt(0) === '#' || /^(mailto|javascript):/i.test(href)) return;
    var u;
    try { u = new URL(href, location.href); } catch (err) { return; }
    if (u.origin !== location.origin) return;          // external
    if (u.href.indexOf(APP_BASE) !== 0) return;        // outside the app
    e.preventDefault();
    navigate(u.href, true);
  });

  window.addEventListener('popstate', function () {
    navigate(location.href, false);
  });

  // Boot the current page: render the shared menu and run any view init. The
  // initial content is already in <main>, so no fetch here.
  var kind = viewKind(location.pathname);
  renderMenu();
  ensureScripts(VIEWS[kind].scripts).then(function () { runInit(kind); });
})();
