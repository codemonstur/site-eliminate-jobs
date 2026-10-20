// Search + pagination for the major groups table. No dependencies.
(function () {
  'use strict';

  var PAGE_SIZES = [10, 25, 50, 100, 250];

  var searchEl = document.getElementById('search');
  var sizeEl = document.getElementById('page-size');
  var statusEl = document.getElementById('status');
  var tbody = document.getElementById('rows');
  var pagEl = document.getElementById('pagination');

  var query = '';
  var page = 1;
  var pageSize = 10;
  var filtered = GROUPS;

  var params = new URLSearchParams(location.search);
  if (params.get('q')) query = params.get('q');
  if (PAGE_SIZES.indexOf(parseInt(params.get('size'), 10)) !== -1) {
    pageSize = parseInt(params.get('size'), 10);
  }
  var urlPage = parseInt(params.get('page'), 10);
  if (urlPage > 0) page = urlPage;

  searchEl.value = query;
  sizeEl.value = String(pageSize);

  function applyFilter() {
    var q = query.trim().toLowerCase();
    if (!q) { filtered = GROUPS; return; }
    filtered = GROUPS.filter(function (g) {
      return g.name.toLowerCase().indexOf(q) !== -1 ||
             g.code.toLowerCase().indexOf(q) !== -1;
    });
  }

  function makeCell(text, className) {
    var td = document.createElement('td');
    td.textContent = text;
    if (className) td.className = className;
    return td;
  }

  function makeLinkCell(href, text, className) {
    var td = document.createElement('td');
    var a = document.createElement('a');
    a.href = href;
    a.textContent = text;
    td.appendChild(a);
    if (className) td.className = className;
    return td;
  }

  function renderRows(slice) {
    var frag = document.createDocumentFragment();
    if (!slice.length) {
      var empty = document.createElement('tr');
      var td = document.createElement('td');
      td.colSpan = 3;
      td.className = 'empty';
      td.textContent = 'No groups match \u201C' + query.trim() + '\u201D';
      empty.appendChild(td);
      frag.appendChild(empty);
    }
    slice.forEach(function (g) {
      var tr = document.createElement('tr');
      tr.appendChild(makeLinkCell('arguments/' + g.code + '.html', g.name.replace(/^\d+\s+/, ''), 'title'));
      tr.appendChild(makeCell(g.code, 'code'));
      tr.appendChild(makeCell(String(g.count), 'num'));
      frag.appendChild(tr);
    });
    tbody.replaceChildren(frag);
  }

  function renderStatus(shown) {
    var total = filtered.length;
    if (total === 0) {
      statusEl.textContent = 'No matches out of ' + GROUPS.length + ' groups.';
      return;
    }
    var from = (page - 1) * pageSize + 1;
    var to = from + shown - 1;
    var text = 'Showing ' + from + '\u2013' + to + ' of ' + total + ' major groups';
    if (total !== GROUPS.length) text += ' (filtered from ' + GROUPS.length + ')';
    statusEl.textContent = text;
  }

  function pageButton(label, targetPage, opts) {
    opts = opts || {};
    var b = document.createElement('button');
    b.type = 'button';
    b.textContent = label;
    if (opts.ariaLabel) b.setAttribute('aria-label', opts.ariaLabel);
    if (opts.current) { b.className = 'current'; b.setAttribute('aria-current', 'page'); }
    else {
      b.addEventListener('click', function () { page = targetPage; render(true); });
    }
    if (opts.disabled) b.disabled = true;
    return b;
  }

  function renderPagination(pages) {
    pagEl.replaceChildren();
    if (pages <= 1 && filtered.length === 0) return;
    pagEl.appendChild(pageButton('\u00AB Prev', page - 1, { disabled: page <= 1, ariaLabel: 'Previous page' }));
    var wanted = [1, pages, page - 1, page, page + 1]
      .filter(function (n) { return n >= 1 && n <= pages; })
      .filter(function (n, i, a) { return a.indexOf(n) === i; })
      .sort(function (a, b) { return a - b; });
    var last = 0;
    wanted.forEach(function (n) {
      if (n - last > 1) {
        var gap = document.createElement('span');
        gap.className = 'gap';
        gap.textContent = '\u2026';
        pagEl.appendChild(gap);
      }
      pagEl.appendChild(pageButton(String(n), n, { current: n === page }));
      last = n;
    });
    pagEl.appendChild(pageButton('Next \u00BB', page + 1, { disabled: page >= pages, ariaLabel: 'Next page' }));
  }

  function syncUrl() {
    var p = new URLSearchParams();
    if (query.trim()) p.set('q', query.trim());
    if (page !== 1) p.set('page', String(page));
    if (pageSize !== 10) p.set('size', String(pageSize));
    var qs = p.toString();
    try { history.replaceState(null, '', qs ? '?' + qs : location.pathname); }
    catch (e) { /* ignore */ }
  }

  function render(scroll) {
    var pages = Math.max(1, Math.ceil(filtered.length / pageSize));
    if (page > pages) page = pages;
    if (page < 1) page = 1;
    var start = (page - 1) * pageSize;
    var slice = filtered.slice(start, start + pageSize);
    renderRows(slice);
    renderStatus(slice.length);
    renderPagination(pages);
    syncUrl();
    if (scroll) document.querySelector('.toolbar').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  searchEl.addEventListener('input', function () { query = searchEl.value; page = 1; applyFilter(); render(false); });
  sizeEl.addEventListener('change', function () { pageSize = parseInt(sizeEl.value, 10); page = 1; render(false); });

  applyFilter();
  render(false);
})();
PY