// Table views for the SPA: the professions list, the major-groups list, and a
// single group's professions. Each entry is a re-runnable init that reads the
// CURRENT DOM (by id) plus the global PROFESSIONS/GROUPS data, so the router
// can call it again after swapping a new view into #app.
(function (global) {
  'use strict';

  var PAGE_SIZES = [10, 25, 50, 100, 250];

  function el(id) { return document.getElementById(id); }

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

  // Shared search + pagination machinery. cfg supplies:
  //   noun    - plural label for status text
  //   colSpan - number of columns (for the empty-state row)
  //   data    - the full array to page over
  //   filter  - (lowercasedQuery) => predicate(item)
  //   row     - (item) => <tr>
  function wireTable(cfg) {
    var searchEl = el('search');
    var sizeEl = el('page-size');
    var statusEl = el('status');
    var tbody = el('rows');
    var pagEl = el('pagination');
    if (!searchEl || !sizeEl || !statusEl || !tbody || !pagEl) return;

    var all = cfg.data;
    var query = '';
    var page = 1;
    var pageSize = 10;
    var filtered = all;

    // Restore state from the URL so filtered pages are linkable.
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
      if (!q) { filtered = all; return; }
      filtered = all.filter(cfg.filter(q));
    }

    function renderRows(slice) {
      var frag = document.createDocumentFragment();
      if (!slice.length) {
        var empty = document.createElement('tr');
        var td = document.createElement('td');
        td.colSpan = cfg.colSpan;
        td.className = 'empty';
        td.textContent = 'No ' + cfg.noun + ' match \u201C' + query.trim() + '\u201D';
        empty.appendChild(td);
        frag.appendChild(empty);
      }
      slice.forEach(function (item) { frag.appendChild(cfg.row(item)); });
      tbody.replaceChildren(frag);
    }

    function renderStatus(shown) {
      var total = filtered.length;
      if (total === 0) {
        statusEl.textContent = 'No matches out of ' + all.length + ' ' + cfg.noun + '.';
        return;
      }
      var from = (page - 1) * pageSize + 1;
      var to = from + shown - 1;
      var text = 'Showing ' + from + '\u2013' + to + ' of ' + total + ' ' + cfg.noun;
      if (total !== all.length) {
        text += ' (filtered from ' + all.length + ')';
      }
      statusEl.textContent = text;
    }

    function pageButton(label, targetPage, opts) {
      opts = opts || {};
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = label;
      if (opts.ariaLabel) b.setAttribute('aria-label', opts.ariaLabel);
      if (opts.current) {
        b.className = 'current';
        b.setAttribute('aria-current', 'page');
      } else {
        b.addEventListener('click', function () {
          page = targetPage;
          render(true);
        });
      }
      if (opts.disabled) b.disabled = true;
      return b;
    }

    function renderPagination(pages) {
      pagEl.replaceChildren();
      if (pages <= 1 && filtered.length === 0) return;

      pagEl.appendChild(pageButton('\u00AB Prev', page - 1, {
        disabled: page <= 1,
        ariaLabel: 'Previous page'
      }));

      // Compact window: 1 … p-1 p p+1 … last
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

      pagEl.appendChild(pageButton('Next \u00BB', page + 1, {
        disabled: page >= pages,
        ariaLabel: 'Next page'
      }));
    }

    function syncUrl() {
      var p = new URLSearchParams();
      if (query.trim()) p.set('q', query.trim());
      if (page !== 1) p.set('page', String(page));
      if (pageSize !== 10) p.set('size', String(pageSize));
      var qs = p.toString();
      // history API can throw on file:// (origin null) — state sync is optional.
      try {
        history.replaceState(null, '', qs ? '?' + qs : location.pathname);
      } catch (e) { /* ignore: opened via file:// */ }
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

      if (scroll) {
        document.querySelector('.toolbar')
          .scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }

    searchEl.addEventListener('input', function () {
      query = searchEl.value;
      page = 1;
      applyFilter();
      render(false);
    });

    sizeEl.addEventListener('change', function () {
      pageSize = parseInt(sizeEl.value, 10);
      page = 1;
      render(false);
    });

    applyFilter();
    render(false);
  }

  var EJTables = {
    // Professions list (4 cols): title -> arguments/<code>.html, code,
    // group -> arguments/<gcode>.html (display name stripped of leading "NN ").
    professions: function () {
      var data = (typeof PROFESSIONS !== 'undefined') ? PROFESSIONS : [];
      wireTable({
        noun: 'professions',
        colSpan: 4,
        data: data,
        filter: function (q) {
          return function (p) {
            return p.title.toLowerCase().indexOf(q) !== -1 ||
                   p.code.toLowerCase().indexOf(q) !== -1 ||
                   p.group.toLowerCase().indexOf(q) !== -1;
          };
        },
        row: function (p) {
          var tr = document.createElement('tr');
          tr.appendChild(makeLinkCell('arguments/' + p.code + '.html', p.title, 'title'));
          tr.appendChild(makeCell(p.code, 'code'));
          tr.appendChild(makeLinkCell(
            'arguments/' + p.group.split(' ')[0] + '.html',
            p.group.replace(/^\d+\s+/, ''),
            'group'
          ));
          var zone = p.jobZone && p.jobZone !== 'n/a' ? p.jobZone : 'n/a';
          tr.appendChild(makeCell(zone, zone === 'n/a' ? 'num na' : 'num'));
          return tr;
        }
      });
    },

    // Major groups list (3 cols): name -> arguments/<code>.html (stripped), code, count.
    groups: function () {
      var src = (typeof GROUPS !== 'undefined') ? GROUPS : [];
      var data = src.slice().sort(function (a, b) {
        var an = a.name.replace(/^\d+\s+/, '');
        var bn = b.name.replace(/^\d+\s+/, '');
        return an.localeCompare(bn);
      });
      wireTable({
        noun: 'major groups',
        colSpan: 3,
        data: data,
        filter: function (q) {
          return function (g) {
            return g.name.toLowerCase().indexOf(q) !== -1 ||
                   g.code.toLowerCase().indexOf(q) !== -1;
          };
        },
        row: function (g) {
          var tr = document.createElement('tr');
          tr.appendChild(makeLinkCell(
            'arguments/' + g.code + '.html',
            g.name.replace(/^\d+\s+/, ''),
            'title'
          ));
          tr.appendChild(makeCell(g.code, 'code'));
          tr.appendChild(makeCell(String(g.count), 'num'));
          return tr;
        }
      });
    },

    // A single group's professions (3 cols), mounted inside <section id="group">
    // on the group detail page. Links are relative to /arguments/.
    groupDetail: function () {
      var root = el('group');
      var all = (typeof PROFESSIONS !== 'undefined') ? PROFESSIONS : [];
      if (!root || !all.length) return;
      var groupCode = root.getAttribute('data-group') || '';
      var members = all.filter(function (p) {
        return p.group.split(' ')[0] === groupCode;
      }).sort(function (a, b) {
        return a.title.localeCompare(b.title, 'en', { sensitivity: 'base' });
      });
      wireTable({
        noun: 'professions',
        colSpan: 3,
        data: members,
        filter: function (q) {
          return function (p) {
            return p.title.toLowerCase().indexOf(q) !== -1 ||
                   p.code.toLowerCase().indexOf(q) !== -1;
          };
        },
        row: function (p) {
          var tr = document.createElement('tr');
          tr.appendChild(makeLinkCell(p.code + '.html', p.title, 'title'));
          tr.appendChild(makeCell(p.code, 'code'));
          var zone = p.jobZone && p.jobZone !== 'n/a' ? p.jobZone : 'n/a';
          tr.appendChild(makeCell(zone, zone === 'n/a' ? 'num na' : 'num'));
          return tr;
        }
      });
    }
  };

  global.EJTables = EJTables;
})(window);
