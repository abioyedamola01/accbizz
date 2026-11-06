/* motion.js: scroll reveal, count-up (unused for now), navigation progress bar.
   Everything is progressive: without JS the .js class is never set, so content is never hidden. */
(function () {
  'use strict';
  var root = document.documentElement;
  var reduce = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  var hasIO = 'IntersectionObserver' in window;

  function toArray(list) { return Array.prototype.slice.call(list); }

  /* ---- Scroll in: [data-reveal], fade plus 20px up, once, about 15% visible, siblings staggered 60ms (max 6) ---- */
  var items = toArray(document.querySelectorAll('[data-reveal]'));
  if (items.length) {
    if (reduce || !hasIO) {
      items.forEach(function (el) { el.classList.add('is-visible'); });
    } else {
      var counts = new Map();
      items.forEach(function (el) {
        var parent = el.parentElement;
        var n = counts.get(parent) || 0;
        if (!el.style.getPropertyValue('--reveal-delay')) el.style.setProperty('--reveal-delay', Math.min(n, 5) * 60 + 'ms');
        counts.set(parent, n + 1);
      });

      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          // Very tall elements may never reach 15% of their own height, so also accept 15% of the viewport
          var enough = entry.intersectionRatio >= 0.15 || entry.intersectionRect.height >= window.innerHeight * 0.15;
          if (!enough) return;
          var el = entry.target;
          el.classList.add('is-visible');
          io.unobserve(el);
          // Drop the stagger delay afterwards so later hover or focus transitions are not delayed
          setTimeout(function () { el.style.setProperty('--reveal-delay', '0ms'); }, 1000);
        });
      }, { threshold: [0, 0.15] });
      items.forEach(function (el) { io.observe(el); });
    }
  }

  /* ---- Count up once: <span data-count-to="1200" data-count-suffix="+">0</span> ---- */
  var counters = toArray(document.querySelectorAll('[data-count-to]'));
  if (counters.length) {
    var fmt = new Intl.NumberFormat(document.documentElement.lang || undefined);
    var render = function (el, value) { el.textContent = fmt.format(Math.round(value)) + (el.getAttribute('data-count-suffix') || ''); };
    if (reduce || !hasIO) {
      counters.forEach(function (el) { render(el, parseFloat(el.getAttribute('data-count-to')) || 0); });
    } else {
      var cio = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          cio.unobserve(el);
          var to = parseFloat(el.getAttribute('data-count-to')) || 0;
          var start = null, dur = 1200;
          (function frame(ts) {
            if (start === null) start = ts;
            var p = Math.min((ts - start) / dur, 1);
            render(el, to * (1 - Math.pow(1 - p, 3)));
            if (p < 1) requestAnimationFrame(frame);
          })(performance.now());
        });
      }, { threshold: 0.4 });
      counters.forEach(function (el) { cio.observe(el); });
    }
  }

  /* ---- Navigation: thin top progress bar instead of a full-screen overlay ---- */
  var bar = document.querySelector('.nav-progress');
  if (bar) {
    var failsafe;
    var start = function () {
      bar.classList.add('is-active');
      clearTimeout(failsafe);
      failsafe = setTimeout(stop, 15000);   // a download or blocked navigation never leaves the bar hanging
    };
    var stop = function () { clearTimeout(failsafe); bar.classList.remove('is-active'); };

    document.addEventListener('click', function (e) {
      if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var a = e.target.closest && e.target.closest('a[href]');
      if (!a || a.hasAttribute('download') || a.hasAttribute('data-no-progress')) return;
      if (a.target && a.target !== '_self') return;
      var url;
      try { url = new URL(a.href, location.href); } catch (err) { return; }
      if (url.origin !== location.origin) return;
      if (url.pathname === location.pathname && url.search === location.search) return; // same page or hash jump
      setTimeout(function () { if (!e.defaultPrevented) start(); }, 0);
    });
    document.addEventListener('submit', function (e) {
      if (e.target.hasAttribute('data-no-progress')) return;
      setTimeout(function () { if (!e.defaultPrevented) start(); }, 0);   // AJAX forms call preventDefault
    });
    window.addEventListener('pageshow', function (e) { if (e.persisted) stop(); });
  }
})();