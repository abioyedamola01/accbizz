/* Reports page (dashboard). Loaded by templates/dashboard/reports.html after Chart.js. Modals follow the Contents pattern (window.dashModal.opened/closed in dashboard.js).
   Defines window.ReportCharts (shared by the enquiries chart here and the Umami chart in dashboard_analytics.js),
   and runs the period filter, the enquiries section and the content health progress. */
(function () {
  'use strict';


  // ---------------------------------------------------------------- shared charts
  window.ReportCharts = (function () {
    var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var live = []; // charts to restyle when the theme changes

    // "2026-10-22" -> "22 Oct" (split by hand so time zones can't shift the day)
    function shortDate(iso) {
      var p = String(iso).split('-');
      if (p.length !== 3) return String(iso);
      return parseInt(p[2], 10) + ' ' + MONTHS[parseInt(p[1], 10) - 1];
    }

    function nextDay(key) {
      var p = key.split('-');
      return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2] + 1)).toISOString().slice(0, 10);
    }

    // The days the page is showing, as "YYYY-MM-DD" days in the dashboard's zone, read from the address:
    // ?range=7d / 30d / 90d (30d when there is none, like the filters) or ?range=custom&from=...&to=...
    // Returns null when it can't tell.
    function rangeBounds() {
      var DT = window.DashboardTime;
      if (!DT) return null;
      var q = new URLSearchParams(window.location.search);
      var range = q.get('range') || '30d';
      if (range === 'custom') {
        var from = DT.dateKey(q.get('from'));
        var to = DT.dateKey(q.get('to'));
        return from && to ? { from: from, to: to } : null;
      }
      var m = /^(\d+)d$/.exec(range);
      if (!m) return null;
      var start = new Date(Date.now() - parseInt(m[1], 10) * 86400000);
      return { from: DT.dateKey(start.toISOString()), to: DT.todayKey() };
    }

    // The server only sends days that have something in them ({ date, count }). Group them by day (a
    // date-time falls on its day in the dashboard's zone, a plain "YYYY-MM-DD" stays as it is), then add
    // the empty days with a count of 0, from the first day of the range to the last.
    function fillDays(points, bounds) {
      var DT = window.DashboardTime;
      var byDay = {};
      (points || []).forEach(function (p) {
        var key = DT ? DT.dateKey(p.date) : String(p.date).slice(0, 10);
        if (!key) return;
        byDay[key] = (byDay[key] || 0) + (Number(p.count) || 0);
      });

      var keys = Object.keys(byDay).sort();
      if (!keys.length) return [];
      var first = keys[0];
      var last = keys[keys.length - 1];
      if (bounds && bounds.from && bounds.from < first) first = bounds.from;
      if (bounds && bounds.to && bounds.to > last) last = bounds.to;

      var days = [];
      for (var key = first, guard = 0; key <= last && guard < 800; key = nextDay(key), guard++) {
        days.push({ date: key, count: byDay[key] || 0 });
      }
      return days;
    }

    // ---- Theme colors, read from the tokens through probe elements (no hex here) ----
    function themeColor(cls, prop, fallback) {
      var probe = document.createElement('span');
      probe.className = cls;
      probe.style.display = 'none';
      document.body.appendChild(probe);
      var value = getComputedStyle(probe)[prop];
      document.body.removeChild(probe);
      return value && value !== 'rgba(0, 0, 0, 0)' && value !== 'transparent' ? value : fallback;
    }

    function palette() {
      var base = getComputedStyle(document.body).color;
      return {
        brand: themeColor('bg-brand-500', 'backgroundColor', base),
        brandFill: themeColor('bg-brand-500/15', 'backgroundColor', 'transparent'),
        ink: themeColor('text-ink', 'color', base),
        muted: themeColor('text-muted', 'color', base),
        line: themeColor('border-line', 'borderTopColor', base)
      };
    }

    function style(chart) {
      var p = palette();
      chart.data.datasets.forEach(function (d) {
        var color = d.role === 'ink' ? p.ink : p.brand;
        d.borderColor = color;
        d.pointBackgroundColor = color;
        d.backgroundColor = d.fill ? p.brandFill : 'transparent';
      });
      var s = chart.options.scales;
      s.x.ticks.color = p.muted;
      s.y.ticks.color = p.muted;
      s.y.grid.color = p.line;
      if (chart.options.plugins.legend.labels) chart.options.plugins.legend.labels.color = p.muted;
    }

    // datasets: [{ label, data, role: 'brand' | 'ink', fill }]. A legend shows when there is more than one.
    function build(canvas, labels, datasets) {
      if (!window.Chart || !canvas) return null;
      var chart = new window.Chart(canvas, {
        type: 'line',
        data: {
          labels: labels,
          datasets: datasets.map(function (d) {
            return {
              label: d.label, data: d.data, role: d.role || 'brand', fill: !!d.fill,
              tension: 0.35, borderWidth: 2,
              pointRadius: labels.length > 31 ? 0 : 3, pointHoverRadius: 5
            };
          })
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: reduceMotion ? false : undefined,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: {
              display: datasets.length > 1,
              position: 'bottom',
              labels: { usePointStyle: true, boxWidth: 8, font: { size: 12 } }
            }
          },
          scales: {
            x: { grid: { display: false }, ticks: { maxTicksLimit: 8, maxRotation: 0, font: { size: 12 } } },
            y: { beginAtZero: true, ticks: { precision: 0, font: { size: 12 } } }
          }
        }
      });
      style(chart);
      chart.update('none');
      live.push(chart);
      return chart;
    }

    // One-series line chart in the brand color
    function line(canvas, labels, values, label) {
      return build(canvas, labels, [{ label: label, data: values, role: 'brand', fill: true }]);
    }

    function lines(canvas, labels, datasets) { return build(canvas, labels, datasets); }

    // Restyle every live chart when the theme changes
    new MutationObserver(function () {
      live = live.filter(function (c) { return c.ctx && c.canvas && c.canvas.isConnected; });
      live.forEach(function (c) { style(c); c.update('none'); });
    }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

    return { line: line, lines: lines, shortDate: shortDate, rangeBounds: rangeBounds, fillDays: fillDays };
  })();

  function $(id) { return document.getElementById(id); }
  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  // ---------------------------------------------------------------- period filter
  (function () {
    var toggle = $('reportCustomToggle');
    var form = $('reportCustomForm');
    var from = $('reportFrom');
    var to = $('reportTo');
    if (!toggle || !form) return;

    toggle.addEventListener('click', function () {
      var open = form.classList.contains('hidden');
      form.classList.toggle('hidden', !open);
      form.classList.toggle('flex', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (open) from.focus();
    });

    // "To" can't be earlier than "From"; "From" can't be later than "To"
    function keepOrder() {
      to.min = from.value || '';
      from.max = to.value || to.max;
    }
    // The days picked here are days in the report's zone (see partials/_time_zone.html), and "today" is today there.
    var DT = window.DashboardTime;
    var fromIso = $('reportFromIso');
    var toIso = $('reportToIso');
    if (DT) { from.max = DT.todayKey(); to.max = DT.todayKey(); }

    // The address holds date-times (UTC). Show the days they fall on in the zone.
    var query = new URLSearchParams(window.location.search);
    if (DT && query.get('range') === 'custom') {
      from.value = DT.dateKey(query.get('from'));
      to.value = DT.dateKey(query.get('to'));
    }

    // Send the start of the first day and the end of the last one (never later than now) as UTC date-times
    form.addEventListener('submit', function () {
      fromIso.value = DT ? DT.dayStartISO(from.value) : from.value;
      toIso.value = DT ? DT.dayEndISO(to.value) : to.value;
    });

    from.addEventListener('change', keepOrder);
    to.addEventListener('change', keepOrder);
    keepOrder();
  })();

  // "(1 Oct to 31 Oct 2026)", from the same day range the charts use, so the label and the charts never disagree
  (function () {
    var out = $('reportRangeText');
    if (!out) return;
    var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    function dayMonth(key) {
      var p = String(key || '').split('-');
      if (p.length !== 3) return '';
      return parseInt(p[2], 10) + ' ' + MONTHS[parseInt(p[1], 10) - 1];
    }
    var bounds = window.ReportCharts.rangeBounds();
    if (!bounds || !bounds.from || !bounds.to) return; // the "selected period" fallback stays
    var fromYear = bounds.from.slice(0, 4);
    var toYear = bounds.to.slice(0, 4);
    out.textContent = dayMonth(bounds.from) + (fromYear !== toYear ? ' ' + fromYear : '') + ' to ' + dayMonth(bounds.to) + ' ' + toYear;
  })();

  // ---------------------------------------------------------------- enquiries
  function readJson(id) {
    var node = $(id);
    if (!node) return [];
    try {
      var value = JSON.parse(node.textContent);
      return Array.isArray(value) ? value : [];
    } catch (e) {
      return [];
    }
  }

  // 1. Messages over time
  (function () {
    var box = $('enqSeriesChart');
    var empty = $('enqSeriesEmpty');
    if (!box || !empty) return;
    var series = readJson('enqSeriesData');
    var total = series.reduce(function (sum, p) { return sum + (Number(p.count) || 0); }, 0);

    if (!total) { box.hidden = true; empty.hidden = false; return; }

    function draw() {
      if (!window.Chart) {
        box.hidden = true;
        empty.textContent = 'The chart could not load. Refresh the page to try again.';
        empty.hidden = false;
        return;
      }
      // Only days with enquiries come from the server; add the empty ones so the line runs through the whole range
      var days = window.ReportCharts.fillDays(series, window.ReportCharts.rangeBounds());
      window.ReportCharts.line(
        $('enqSeriesCanvas'),
        days.map(function (d) { return window.ReportCharts.shortDate(d.date); }),
        days.map(function (d) { return d.count; }),
        'Messages'
      );
    }
    draw();
  })();

  // 2. Enquiries by service: the busiest 5 + "Other", everything in a modal
  (function () {
    var TOP = 5;
    var list = $('enqServiceList');
    if (!list) return;

    var rows = Array.prototype.map.call(list.children, function (li, i) {
      return { title: li.dataset.title || '', count: Number(li.dataset.count) || 0, order: i };
    });
    rows.sort(function (a, b) { return (b.count - a.count) || (a.order - b.order); });

    // One row: name, count (and share when asked for), and a bar
    function serviceRow(title, count, max, options) {
      options = options || {};
      var li = el('li');
      var top = el('div', 'flex items-baseline justify-between gap-3 text-small');
      var name = el('span', 'min-w-0 truncate ' + (options.muted ? 'text-muted' : 'text-ink'), title);
      name.title = title;
      var amount = el('span', 'shrink-0 flex items-baseline gap-3 font-semibold text-ink');
      amount.appendChild(el('span', '', String(count)));
      if (options.share !== undefined) amount.appendChild(el('span', 'text-caption font-normal text-muted', options.share + '%'));
      top.appendChild(name);
      top.appendChild(amount);

      var track = el('div', 'mt-2 h-2 overflow-hidden rounded-full bg-raised');
      var bar = el('div', 'h-2 rounded-full ' + (options.muted ? 'bg-muted/50' : 'bg-brand-500'));
      bar.style.width = (count && max ? Math.max(4, Math.round((count / max) * 100)) : 0) + '%';
      track.appendChild(bar);
      li.appendChild(top);
      li.appendChild(track);
      return li;
    }

    var total = rows.reduce(function (sum, r) { return sum + r.count; }, 0);

    // A short list stays as the page rendered it: only the bar widths are set
    if (rows.length <= TOP + 1) {
      var max = rows.length ? rows[0].count : 0;
      if (!max) return;
      Array.prototype.forEach.call(list.children, function (li) {
        var count = Number(li.dataset.count) || 0;
        li.querySelector('[data-bar]').style.width = (count ? Math.max(4, Math.round((count / max) * 100)) : 0) + '%';
      });
      return;
    }

    // A long one: the busiest 5, then everything else added up as one row
    var shown = rows.slice(0, TOP);
    var rest = rows.slice(TOP);
    var otherCount = rest.reduce(function (sum, r) { return sum + r.count; }, 0);
    var biggest = Math.max(shown[0].count, otherCount); // so no bar runs past its track

    while (list.firstChild) list.removeChild(list.firstChild);
    shown.forEach(function (r) { list.appendChild(serviceRow(r.title, r.count, biggest)); });
    list.appendChild(serviceRow('Other (' + rest.length + ' services)', otherCount, biggest, { muted: true }));

    var viewAll = el('button', 'btn btn-link btn-sm self-start', 'View all ' + rows.length + ' services');
    viewAll.type = 'button';
    viewAll.setAttribute('aria-haspopup', 'dialog');
    list.insertAdjacentElement('afterend', viewAll);

    // The modal with every service
    var modal = $('enqServicesModal');
    var modalList = $('enqServicesList');
    var maxCount = rows[0].count;

    function fillModal() {
      while (modalList.firstChild) modalList.removeChild(modalList.firstChild);
      rows.forEach(function (r) {
        modalList.appendChild(serviceRow(r.title, r.count, maxCount, { share: total ? Math.round((r.count / total) * 100) : undefined }));
      });
      $('enqServicesSummary').textContent =
        rows.length + ' services \u00b7 ' + total + ' enquir' + (total === 1 ? 'y' : 'ies') + ' in the selected period';
    }

    function closeModal() { window.dashModal.close(modal); }
    viewAll.addEventListener('click', function () {
      fillModal();
      window.dashModal.open(modal, { opener: viewAll, focus: $('enqServicesClose'), onRequestClose: closeModal });
      modalList.scrollTop = 0;
    });
    $('enqServicesClose').addEventListener('click', closeModal);
    $('enqServicesOverlay').addEventListener('click', closeModal);
  })();

  // 3. Busiest days: bar widths relative to the busiest day; the busiest day is full strength
  (function () {
    var rows = document.querySelectorAll('#enqWeekdayList > li');
    var max = 0;
    rows.forEach(function (li) { max = Math.max(max, Number(li.dataset.count) || 0); });
    if (!max) return;
    rows.forEach(function (li) {
      var count = Number(li.dataset.count) || 0;
      var bar = li.querySelector('[data-bar]');
      bar.style.width = (count ? Math.max(4, Math.round((count / max) * 100)) : 0) + '%';
      if (count !== max) bar.classList.add('opacity-50');
    });
  })();

  // 4. Attended per staff: the full list in a modal (only rendered when there are more than 5)
  (function () {
    var modal = $('attStaffModal');
    var openBtn = $('attStaffViewAll');
    var closeBtn = $('attStaffClose');
    if (!modal || !openBtn || !closeBtn) return;

    function closeModal() { window.dashModal.close(modal); }
    openBtn.addEventListener('click', function () {
      window.dashModal.open(modal, { opener: openBtn, focus: closeBtn, onRequestClose: closeModal });
    });
    closeBtn.addEventListener('click', closeModal);
    $('attStaffOverlay').addEventListener('click', closeModal);
  })();

  // ---------------------------------------------------------------- content health
  (function () {
    // Labels the template doesn't know: "opening_hours" -> "Opening hours"
    document.querySelectorAll('#healthChecklist [data-prettify]').forEach(function (node) {
      node.textContent = node.textContent.replace(/_/g, ' ');
    });

    var rows = document.querySelectorAll('#healthChecklist > li');
    if (!rows.length) return;
    var done = 0;
    rows.forEach(function (li) { if (li.dataset.ok === '1') done++; });
    var pct = Math.round((done / rows.length) * 100);

    $('healthProgressText').textContent = done + ' of ' + rows.length + ' complete';
    $('healthProgressBar').style.width = pct + '%';
    $('healthProgress').setAttribute('aria-valuenow', String(pct));
    $('healthAllDone').hidden = done !== rows.length;
  })();
})();