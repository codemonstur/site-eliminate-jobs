// Lightweight inline navigation for the three main pages.
// Keeps the sidebar visible and avoids full reloads. Falls back to normal
// navigation if anything fails.
(function () {
  'use strict';

  var SHELL_PAGES = { 'index.html': 1, 'professions.html': 1, 'groups.html': 1 };
  var SCRIPTS = {
    'professions.html': ['professions.js', 'app.js'],
    'groups.html': ['groups.js', 'groups-app.js']
  };
  var loadedScripts = {};
  if (typeof PROFESSIONS !== 'undefined') loadedScripts['professions.js'] = true;
  if (typeof GROUPS !== 'undefined') loadedScripts['groups.js'] = true;

  function isShell(href) {
    try {
      var u = new URL(href, location.href);
      if (u.origin !== location.origin) return false;
      var name = u.pathname.split('/').pop();
      return !!SHELL_PAGES[name];
    } catch (e) { return false; }
  }

  function loadScript(src) {
    if (loadedScripts[src]) return Promise.resolve();
    // already in DOM?
    var existing = document.querySelector('script[src="' + src + '"]');
    if (existing) { loadedScripts[src] = true; return Promise.resolve(); }
    return new Promise(function (resolve) {
      var s = document.createElement('script');
      s.src = src;
      s.onload = function () { loadedScripts[src] = true; resolve(); };
      s.onerror = function () { resolve(); };
      document.body.appendChild(s);
    });
  }

  function loadScripts(list) {
    var p = Promise.resolve();
    list.forEach(function (src) {
      p = p.then(function () { return loadScript(src); });
    });
    return p;
  }

  function setActive(name) {
    document.querySelectorAll('#side-menu a').forEach(function (a) {
      var n = (a.getAttribute('href') || '').split('/').pop();
      a.classList.toggle('active', n === name);
    });
  }

  async function navigate(url, push) {
    try {
      var res = await fetch(url);
      if (!res.ok) throw new Error(res.status);
      var html = await res.text();
      var doc = new DOMParser().parseFromString(html, 'text/html');
      var main = doc.querySelector('main');
      if (!main) throw new Error('no main');
      var current = document.querySelector('main');
      current.innerHTML = main.innerHTML;
      if (doc.title) document.title = doc.title;
      var name = url.split('/').pop().split('?')[0];
      setActive(name);
      if (push) history.pushState({ url: url }, '', url);
      // load page scripts
      var scripts = SCRIPTS[name];
      if (scripts) await loadScripts(scripts);
    } catch (e) {
      location.href = url;
    }
  }

  document.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a') : null;
    if (!a) return;
    if (a.target === '_blank') return;
    var href = a.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('mailto:')) return;
    if (!isShell(href)) return;
    e.preventDefault();
    navigate(href, true);
  });

  window.addEventListener('popstate', function (e) {
    var url = (e.state && e.state.url) ? e.state.url : location.href;
    if (isShell(url)) navigate(url, false);
  });
})();
PY