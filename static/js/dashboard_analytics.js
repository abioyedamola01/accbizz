/* Website analytics (Umami) on the Reports page. Loaded by templates/dashboard/reports.html after dashboard_reports.js
   (needs window.ReportCharts and window.DashboardTime). Markup: partials/reports/_analytics.html. */
(function () {
  'use strict';
  (function () {
    var root = document.getElementById('analyticsSection');
    if (!root) return;

    var TZ = (window.DashboardTime && window.DashboardTime.TZ) || 'Africa/Lagos'; // set in partials/_time_zone.html
    var DAY = 86400000;

    // ---- Labels you can edit ----------------------------------------------
    var EVENT_LABELS = {
      'contact-form-success': 'Contact form sent',
      'testimonial-form-success': 'Testimonial submitted'
    };
    var FORM_CONTACT = 'contact-form-success';
    var FORM_TESTIMONIAL = 'testimonial-form-success';
    // ------------------------------------------------------------------------

    function $(id) { return document.getElementById(id); }
    function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }
    function el(tag, className, text) {
      var node = document.createElement(tag);
      if (className) node.className = className;
      if (text !== undefined) node.textContent = text;
      return node;
    }

    var states = { loading: $('analyticsLoading'), error: $('analyticsError'), content: $('analyticsContent') };
    function show(name) {
      Object.keys(states).forEach(function (key) { states[key].hidden = key !== name; });
    }

    var chart = null;
    var requestId = 0;

    // ---- Formatting ----
    function fmtNumber(n) { return (Number(n) || 0).toLocaleString(); }
    function fmtPercent(n) { return (Math.round((Number(n) || 0) * 10) / 10) + '%'; }
    function fmtDuration(seconds) {
      var s = Math.round(Number(seconds) || 0);
      if (s < 60) return s + 's';
      var m = Math.floor(s / 60);
      if (m < 60) return m + 'm ' + (s % 60) + 's';
      return Math.floor(m / 60) + 'h ' + (m % 60) + 'm';
    }
    function lagos(opts, locale) { return new Intl.DateTimeFormat(locale || 'en-GB', Object.assign({ timeZone: TZ }, opts)); }
    var dateTimeFmt = lagos({ day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit', hour12: true });
    var dayFmt = lagos({ day: 'numeric', month: 'short' });
    var dayYearFmt = lagos({ day: 'numeric', month: 'short', year: 'numeric' });
    var hourFmt = lagos({ hour: 'numeric', hour12: true });
    var dayHourFmt = lagos({ day: 'numeric', month: 'short', hour: 'numeric', hour12: true });
    var monthFmt = lagos({ month: 'short', year: 'numeric' });
    var dayKeyFmt = lagos({ year: 'numeric', month: '2-digit', day: '2-digit' }, 'en-CA'); // 2026-10-25

    function fmtDateTime(iso) {
      var d = new Date(iso);
      return isNaN(d.getTime()) ? '' : dateTimeFmt.format(d);
    }
    function titleCase(text) {
      text = String(text).replace(/[-_]+/g, ' ').trim();
      return text.charAt(0).toUpperCase() + text.slice(1);
    }
    var regionNames = null;
    try { regionNames = new Intl.DisplayNames(['en'], { type: 'region' }); } catch (e) { regionNames = null; }
    function countryName(code) {
      try { return (regionNames && regionNames.of(String(code).toUpperCase())) || code; } catch (e) { return code; }
    }

    // ---- Response helpers ----
    // Umami parts look like { response, error, status_code }. Returns the response, or null if it failed.
    function resp(part) {
      if (!part || part.error) return null;
      if (part.status_code && Number(part.status_code) >= 400) return null;
      return part.response === undefined ? null : part.response;
    }

    // events is ONE page of rows. Partial = not every event is in the list.
    function partialInfo(events) {
      if (!events) return null;
      var rows = events.data || [];
      var total = Number(events.count) || rows.length;
      if (events.isCapped || total > rows.length) return { shown: rows.length, total: total, capped: !!events.isCapped };
      return null;
    }
    function setBadge(id, info) {
      var slot = $(id);
      clear(slot);
      if (!info) return;
      var pill = el('span', 'badge', 'Latest data');
      pill.title = 'Based on the latest ' + info.shown + ' of ' + (info.capped ? 'at least ' : '') + info.total + ' events, not the whole period.';
      slot.appendChild(pill);
    }

    // ---- "vs prior" lines (comparison holds the previous period's totals) ----
    function setDelta(id, cur, prev, goodUp) {
      var node = $(id);
      node.textContent = '';
      prev = Number(prev) || 0;
      cur = Number(cur) || 0;
      if (!(prev > 0)) return;
      var pct = Math.round(((cur - prev) / prev) * 100);
      if (pct === 0) { node.className = 'min-h-4 text-caption font-medium text-muted'; node.textContent = 'No change vs prior'; return; }
      var up = pct > 0;
      var good = goodUp ? up : !up;
      node.className = 'min-h-4 text-caption font-medium ' + (good ? 'text-success-fg' : 'text-danger-fg');
      node.textContent = (up ? '\u25B2 ' : '\u25BC ') + Math.abs(pct) + '% vs prior';
    }
    function setPointDelta(id, cur, prev, prevVisits, goodUp) {
      var node = $(id);
      node.textContent = '';
      if (!(Number(prevVisits) > 0)) return;
      var diff = Math.round((cur - prev) * 10) / 10;
      if (diff === 0) { node.className = 'min-h-4 text-caption font-medium text-muted'; node.textContent = 'No change vs prior'; return; }
      var up = diff > 0;
      var good = goodUp ? up : !up;
      node.className = 'min-h-4 text-caption font-medium ' + (good ? 'text-success-fg' : 'text-danger-fg');
      node.textContent = (up ? '\u25B2 ' : '\u25BC ') + Math.abs(diff) + ' pts vs prior';
    }

    // ---- Summary cards ----
    function renderStats(stats) {
      var err = $('anStatsError');
      if (!stats) { err.hidden = false; return; }
      err.hidden = true;

      var prev = stats.comparison || {};
      var visits = Number(stats.visits) || 0;
      var prevVisits = Number(prev.visits) || 0;
      var avg = visits ? (Number(stats.totaltime) || 0) / visits : 0;
      var prevAvg = prevVisits ? (Number(prev.totaltime) || 0) / prevVisits : 0;
      var bounce = visits ? ((Number(stats.bounces) || 0) / visits) * 100 : 0;
      var prevBounce = prevVisits ? ((Number(prev.bounces) || 0) / prevVisits) * 100 : 0;

      $('anVisitors').textContent = fmtNumber(stats.visitors);
      setDelta('anVisitorsDelta', stats.visitors, prev.visitors, true);
      $('anViews').textContent = fmtNumber(stats.pageviews);
      setDelta('anViewsDelta', stats.pageviews, prev.pageviews, true);
      $('anVisits').textContent = fmtNumber(stats.visits);
      setDelta('anVisitsDelta', stats.visits, prev.visits, true);
      $('anDuration').textContent = fmtDuration(avg);
      setDelta('anDurationDelta', avg, prevAvg, true);
      $('anBounce').textContent = fmtPercent(bounce);
      setPointDelta('anBounceDelta', bounce, prevBounce, prevVisits, false);
    }

    // ---- Chart ----
    // Umami sends only the time buckets that had traffic. Hourly buckets over a long range are
    // summed into Lagos days (page views only, because summing sessions would double count).
    function dayKey(t) { return dayKeyFmt.format(new Date(t)); }
    function keyToDate(key) { return new Date(key + 'T12:00:00Z'); }
    function detectUnit(times) {
      if (times.length < 2) return 'hour';
      var hours = times.map(function (t) { return new Date(t).getUTCHours(); });
      var sameHour = hours.every(function (h) { return h === hours[0]; });
      if (!sameHour) return 'hour';
      var minGap = Infinity;
      for (var i = 1; i < times.length; i++) minGap = Math.min(minGap, times[i] - times[i - 1]);
      return minGap >= 27 * DAY ? 'month' : 'day';
    }
    // Every Lagos day from the range start to its end (widened to cover the data), up to 400 days.
    function dayKeys(range, times) {
      var from = range && Date.parse(range.from_date);
      var to = range && Date.parse(range.to_date);
      var lo = times[0], hi = times[times.length - 1];
      if (!isNaN(from) && !isNaN(to) && to > from) { lo = Math.min(lo, from); hi = Math.max(hi, to); }
      var startKey = dayKey(lo), endKey = dayKey(hi);
      var keys = [];
      for (var t = keyToDate(startKey).getTime(); keys.length < 400; t += DAY) {
        var key = new Date(t).toISOString().slice(0, 10);
        if (key > endKey) break;
        keys.push(key);
      }
      return keys;
    }
    function buildSeries(pv, range) {
      var views = (pv && pv.pageviews) || [];
      var sessions = (pv && pv.sessions) || [];
      var viewMap = {}, sessMap = {}, set = {};
      views.forEach(function (pt) { var t = Date.parse(pt.x); if (!isNaN(t)) { viewMap[t] = Number(pt.y) || 0; set[t] = 1; } });
      sessions.forEach(function (pt) { var t = Date.parse(pt.x); if (!isNaN(t)) { sessMap[t] = Number(pt.y) || 0; set[t] = 1; } });
      var times = Object.keys(set).map(Number).sort(function (a, b) { return a - b; });
      if (!times.length) return null;

      var unit = detectUnit(times);
      var fromHours = unit === 'hour' && (times[times.length - 1] - times[0]) > 3 * DAY;

      if (unit === 'day' || fromHours) {
        var dayViews = {}, daySess = {};
        times.forEach(function (t) {
          var k = dayKey(t);
          dayViews[k] = (dayViews[k] || 0) + (viewMap[t] || 0);
          daySess[k] = (daySess[k] || 0) + (sessMap[t] || 0);
        });
        var keys = dayKeys(range, times);
        return {
          labels: keys.map(function (k) { return dayFmt.format(keyToDate(k)); }),
          views: keys.map(function (k) { return dayViews[k] || 0; }),
          sessions: fromHours ? null : keys.map(function (k) { return daySess[k] || 0; })
        };
      }

      if (unit === 'hour' && (times[times.length - 1] - times[0]) / 3600000 <= 400) {
        var filled = [];
        for (var t = times[0]; t <= times[times.length - 1]; t += 3600000) filled.push(t);
        times = filled;
      }
      var sameDay = dayFmt.format(new Date(times[0])) === dayFmt.format(new Date(times[times.length - 1]));
      return {
        labels: times.map(function (t) {
          var d = new Date(t);
          if (unit === 'month') return monthFmt.format(d);
          return sameDay ? hourFmt.format(d) : dayHourFmt.format(d);
        }),
        views: times.map(function (t) { return viewMap[t] || 0; }),
        sessions: times.map(function (t) { return sessMap[t] || 0; })
      };
    }
    function renderChart(pv, range) {
      var box = $('anChartBox');
      var empty = $('anChartEmpty');
      if (chart) { chart.destroy(); chart = null; }
      var series = buildSeries(pv, range);
      var total = series ? series.views.reduce(function (a, b) { return a + b; }, 0) : 0;
      if (!total) { box.hidden = true; empty.hidden = false; return; }
      if (!window.ReportCharts || !window.Chart || !window.ReportCharts.lines) {
        box.hidden = true;
        empty.textContent = 'The chart could not load. Refresh the page to try again.';
        empty.hidden = false;
        return;
      }
      box.hidden = false;
      empty.hidden = true;
      var datasets = [{ label: 'Page views', data: series.views, role: 'brand', fill: true }];
      if (series.sessions) datasets.push({ label: 'Sessions', data: series.sessions, role: 'ink', fill: false });
      chart = window.ReportCharts.lines($('anCanvas'), series.labels, datasets);
    }

    // ---- Bar lists ----
    // rows: [{ label, sub, value, unit, detail }]. null means the part failed to load.
    function renderBars(listId, emptyId, rows, emptyText) {
      var ul = $(listId);
      var empty = $(emptyId);
      clear(ul);
      if (rows === null) {
        empty.textContent = "Couldn't load this card. Try refreshing.";
        empty.hidden = false;
        return;
      }
      empty.textContent = emptyText;
      empty.hidden = !!rows.length;
      var max = 0;
      rows.forEach(function (r) { max = Math.max(max, r.value); });
      rows.forEach(function (r) {
        var li = el('li');
        var top = el('div', 'flex items-baseline justify-between gap-3 text-small');
        var name = el('span', 'min-w-0 truncate text-ink', r.label);
        name.title = r.sub ? r.label + ' (' + r.sub + ')' : r.label;
        top.appendChild(name);
        var amount = el('span', 'shrink-0 flex items-baseline gap-1 font-semibold text-ink');
        amount.appendChild(el('span', '', fmtNumber(r.value)));
        if (r.unit) amount.appendChild(el('span', 'text-caption font-normal text-muted', r.unit));
        top.appendChild(amount);
        var track = el('div', 'mt-2 h-2 overflow-hidden rounded-full bg-raised');
        var bar = el('div', 'h-2 rounded-full bg-brand-500');
        bar.style.width = (r.value && max ? Math.max(4, Math.round((r.value / max) * 100)) : 0) + '%';
        track.appendChild(bar);
        li.appendChild(top);
        if (r.detail) li.appendChild(el('p', 'text-caption text-muted', r.detail));
        li.appendChild(track);
        ul.appendChild(li);
      });
    }
    function num(x) { return Number(x) || 0; }
    function plural(n, word) { return fmtNumber(n) + ' ' + word + (n === 1 ? '' : 's'); }
    function metricRows(part, mapRow) {
      var list = resp(part);
      if (list === null || !Array.isArray(list)) return null;
      return list.map(mapRow)
        .filter(function (r) { return r.value > 0; })
        .sort(function (a, b) { return b.value - a.value; })
        .slice(0, 8);
    }
    function pageLabel(path) {
      path = String(path || '/');
      return path === '/' ? 'Home' : path;
    }

    // ---- Recent activity (from the events list) ----
    function renderRecent(rows) {
      var ul = $('anRecent');
      clear(ul);
      var sorted = rows.slice().sort(function (a, b) { return Date.parse(b.createdAt) - Date.parse(a.createdAt); }).slice(0, 8);
      $('anRecentEmpty').hidden = !!sorted.length;
      sorted.forEach(function (r) {
        var isEvent = Number(r.eventType) === 2 && r.eventName;
        var li = el('li', 'flex items-start gap-3 py-3');
        li.appendChild(el('span', 'mt-2 h-2 w-2 shrink-0 rounded-full ' + (isEvent ? 'bg-brand-500' : 'bg-muted/50')));

        var mid = el('div', 'min-w-0 flex-1');
        mid.appendChild(el('p', 'truncate text-small ' + (isEvent ? 'font-semibold text-ink' : 'text-muted'),
          isEvent ? (EVENT_LABELS[r.eventName] || titleCase(r.eventName)) : (r.pageTitle || pageLabel(r.urlPath))));
        var place = [r.city, r.country ? countryName(r.country) : ''].filter(Boolean).join(', ');
        var device = [r.device, r.browser].filter(Boolean).map(titleCase).join(' \u00b7 ');
        mid.appendChild(el('p', 'truncate text-caption text-muted', [pageLabel(r.urlPath), place, device].filter(Boolean).join(' \u00b7 ')));
        li.appendChild(mid);

        li.appendChild(el('span', 'shrink-0 text-caption text-muted', fmtDateTime(r.createdAt)));
        ul.appendChild(li);
      });
    }

    function renderRange(range) {
      var label = $('analyticsRange');
      var from = range && new Date(range.from_date);
      var to = range && new Date(range.to_date);
      if (!from || !to || isNaN(from.getTime()) || isNaN(to.getTime())) { label.textContent = ''; return; }
      label.textContent = dayFmt.format(from) + ' to ' + dayYearFmt.format(to);
    }

    function render(data) {
      var pub = data.public_site_analytics_data;
      if (!pub || typeof pub !== 'object' || !Object.keys(pub).length) { fail('Analytics data is unavailable.'); return; }

      renderRange(data.range_info);

      var stats = resp(pub.stats);
      var eventsPart = resp(pub.events);
      var rows = (eventsPart && eventsPart.data) || [];
      var partial = partialInfo(eventsPart);                                   // rows incomplete (count > rows, or capped)
      var cappedInfo = eventsPart && eventsPart.isCapped ? partial : null;     // the server said the list is capped

      // Nothing at all in this period
      var pageviews = stats ? Number(stats.pageviews) || 0 : 0;
      var visits = stats ? Number(stats.visits) || 0 : 0;
      if (stats && !pageviews && !visits) {
        $('anEmpty').hidden = false;
        $('anBody').hidden = true;
        show('content');
        return;
      }
      $('anEmpty').hidden = true;
      $('anBody').hidden = false;

      renderStats(stats);
      renderChart(resp(pub.page_views), data.range_info);

      // data_by_metrics rows: { name, pageviews, visitors, ... } (numbers can arrive as strings)
      var metrics = pub.data_by_metrics || {};
      renderBars('anPages', 'anPagesEmpty',
        metricRows(metrics.path, function (r) {
          return { label: pageLabel(r.name), sub: r.name, value: num(r.pageviews), unit: num(r.pageviews) === 1 ? 'view' : 'views', detail: plural(num(r.visitors), 'visitor') };
        }), 'No page views yet.');
      renderBars('anCountries', 'anCountriesEmpty',
        metricRows(metrics.country, function (r) {
          return { label: countryName(r.name), sub: r.name, value: num(r.visitors), unit: num(r.visitors) === 1 ? 'visitor' : 'visitors', detail: plural(num(r.pageviews), 'page view') };
        }), 'No location data yet.');
      renderBars('anCities', 'anCitiesEmpty',
        metricRows(metrics.city, function (r) {
          return { label: r.country ? r.name + ', ' + countryName(r.country) : r.name, value: num(r.visitors), unit: num(r.visitors) === 1 ? 'visitor' : 'visitors', detail: plural(num(r.pageviews), 'page view') };
        }), 'No location data yet.');

      // Form submissions: exact counts from data_by_metrics.event (pageviews = number of events).
      // If that part is missing, fall back to counting the events list (then it can be partial).
      var contact = 0, testimonials = 0, formsKnown = false, formsPartial = null;
      var eventMetric = resp(metrics.event);
      if (Array.isArray(eventMetric)) {
        formsKnown = true;
        eventMetric.forEach(function (r) {
          if (r.name === FORM_CONTACT) contact = num(r.pageviews);
          if (r.name === FORM_TESTIMONIAL) testimonials = num(r.pageviews);
        });
      } else if (eventsPart) {
        formsKnown = true;
        formsPartial = partial;
        rows.forEach(function (r) {
          if (r.eventName === FORM_CONTACT) contact++;
          if (r.eventName === FORM_TESTIMONIAL) testimonials++;
        });
      }
      $('anFormsError').hidden = formsKnown;
      $('anFormContact').textContent = formsKnown ? fmtNumber(contact) : '-';
      $('anFormTestimonial').textContent = formsKnown ? fmtNumber(testimonials) : '-';
      $('anFormRate').textContent = formsKnown && visits ? fmtPercent((contact / visits) * 100) : '-';
      setBadge('anFormsBadge', formsPartial);

      renderRecent(rows);
      $('anRecentEmpty').textContent = eventsPart ? 'No activity yet.' : "Couldn't load recent activity.";
      setBadge('anRecentBadge', cappedInfo);

      var note = $('anNote');
      var flagged = [];
      if (formsPartial) flagged.push('Form submissions');
      if (cappedInfo) flagged.push('Recent activity');
      if (flagged.length) {
        note.textContent = 'Umami returned only the latest ' + partial.shown + ' of ' + (partial.capped ? 'at least ' : '') + partial.total +
          ' events' + (partial.capped ? ' (capped)' : '') + ', so the cards marked "Latest data" (' +
          flagged.join(' and ') + ') cover just those, not the whole period.';
        note.hidden = false;
      } else {
        note.hidden = true;
      }

      show('content');
    }

    function fail(message) {
      $('analyticsErrorMsg').textContent = message || "Couldn't load analytics. Check your connection and try again.";
      show('error');
    }

    // ---- Loading ----
    function setBusy(busy) {
      $('analyticsRefresh').disabled = busy;
      $('analyticsRefreshIcon').classList.toggle('animate-spin', busy);
    }

    function load(refresh) {
      var id = ++requestId;
      setBusy(true);
      show('loading');

      // Same range as the page: copy ?range=, ?from=, ?to= from this page's URL.
      var url = new URL(root.dataset.url, window.location.origin);
      new URLSearchParams(window.location.search).forEach(function (value, key) { url.searchParams.set(key, value); });
      if (refresh) url.searchParams.set('refresh', '1');

      fetch(url.toString(), {
        credentials: 'same-origin',
        headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }
      })
        .then(function (res) {
          return res.json().catch(function () { return null; }).then(function (data) { return { ok: res.ok, data: data }; });
        })
        .then(function (r) {
          if (id !== requestId) return;          // a newer request replaced this one
          if (!r.ok || !r.data || r.data.ok === false) { fail(r.data && r.data.message); return; }
          render(r.data);
        })
        .catch(function () { if (id === requestId) fail(); })
        .then(function () { if (id === requestId) setBusy(false); });
    }

    $('analyticsRefresh').addEventListener('click', function () { load(true); });
    $('analyticsRetry').addEventListener('click', function () { load(false); });
    load(false);
  })();
})();