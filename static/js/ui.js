/* ui.js: theme control, navbar behavior, back-to-top, testimonial slider. */
(function () {
  'use strict';
  var root = document.documentElement;
  function qs(sel, ctx) { return (ctx || document).querySelector(sel); }
  function qsa(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }
  var reduced = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  /* =========================== Theme: light, dark, system =========================== */
  var KEY = 'theme';
  var mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

  function getPref() {
    try { var v = localStorage.getItem(KEY); return v === 'light' || v === 'dark' ? v : 'system'; } catch (e) { return 'system'; }
  }
  function applyTheme(pref) {
    var theme = pref === 'system' ? (mq && mq.matches ? 'dark' : 'light') : pref;
    root.setAttribute('data-theme', theme);
    root.setAttribute('data-theme-pref', pref);
    var meta = qs('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', meta.getAttribute('data-' + theme) || meta.getAttribute('content'));
    qsa('[data-theme-option]').forEach(function (b) {
      b.setAttribute('aria-pressed', b.getAttribute('data-theme-option') === pref ? 'true' : 'false');
    });
  }
  function setPref(pref) {
    try { if (pref === 'system') localStorage.removeItem(KEY); else localStorage.setItem(KEY, pref); } catch (e) {}
    applyTheme(pref);
  }
  applyTheme(getPref());
  if (mq) {
    var onScheme = function () { if (getPref() === 'system') applyTheme('system'); };
    if (mq.addEventListener) mq.addEventListener('change', onScheme); else if (mq.addListener) mq.addListener(onScheme);
  }
  window.addEventListener('storage', function (e) { if (e.key === KEY) applyTheme(getPref()); });

  /* =========================== Navbar =========================== */
  var header = qs('#siteHeader');
  var navBtn = qs('#navToggleBtn');
  var panel = qs('#mobileNav');
  var themeBtn = qs('[data-theme-toggle]');
  var themeMenu = qs('[data-theme-menu]');

  function setNav(open, returnFocus) {
    if (!navBtn || !panel) return;
    panel.classList.toggle('is-open', open);
    navBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (!open && returnFocus) navBtn.focus();
  }
  function setThemeMenu(open, returnFocus) {
    if (!themeBtn || !themeMenu) return;
    themeMenu.classList.toggle('is-open', open);
    themeBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) {
      var current = qs('[aria-pressed="true"]', themeMenu) || qs('button', themeMenu);
      if (current) current.focus();
    } else if (returnFocus) themeBtn.focus();
  }

  if (navBtn && panel) {
    navBtn.addEventListener('click', function () { setThemeMenu(false); setNav(!panel.classList.contains('is-open')); });
    if (window.matchMedia) {
      window.matchMedia('(min-width: 1024px)').addEventListener('change', function (e) { if (e.matches) setNav(false); });
    }
  }
  if (themeBtn && themeMenu) {
    themeBtn.addEventListener('click', function () { setNav(false); setThemeMenu(!themeMenu.classList.contains('is-open')); });
    themeMenu.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
      e.preventDefault();
      var opts = qsa('button', themeMenu);
      var i = opts.indexOf(document.activeElement);
      i = e.key === 'ArrowDown' ? (i + 1) % opts.length : (i - 1 + opts.length) % opts.length;
      opts[i].focus();
    });
  }
  document.addEventListener('click', function (e) {
    var opt = e.target.closest && e.target.closest('[data-theme-option]');
    if (opt) { setPref(opt.getAttribute('data-theme-option')); setThemeMenu(false, true); return; }
    // Outside click closes whichever menu is open
    if (themeMenu && themeMenu.classList.contains('is-open') && !themeMenu.contains(e.target) && !themeBtn.contains(e.target)) setThemeMenu(false);
    if (panel && panel.classList.contains('is-open') && !header.contains(e.target)) setNav(false);
    // Tapping a link in the mobile panel closes it (same-page hashes)
    if (panel && panel.contains(e.target) && e.target.closest('a')) setNav(false);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (themeMenu && themeMenu.classList.contains('is-open')) setThemeMenu(false, true);
    else if (panel && panel.classList.contains('is-open')) setNav(false, true);
  });

  /* Header shadow and back-to-top use sentinels, no scroll listeners */
  if ('IntersectionObserver' in window) {
    var s1 = qs('[data-scroll-sentinel]');
    if (s1 && header) new IntersectionObserver(function (en) { header.classList.toggle('is-scrolled', !en[0].isIntersecting); }).observe(s1);
    var s2 = qs('[data-top-sentinel]');
    var toTop = qs('[data-to-top]');
    if (s2 && toTop) new IntersectionObserver(function (en) {
      var show = !en[0].isIntersecting;
      toTop.classList.toggle('is-visible', show);
      if (show) toTop.removeAttribute('tabindex'); else toTop.setAttribute('tabindex', '-1');
    }).observe(s2);
  }

  /* =========================== Testimonial slider =========================== */
  function initSlider(rootEl) {
    if (rootEl.dataset.tstReady) return;   // already set up (partial included twice, or by an older inline script)

    var stage = qs('.tst-stage', rootEl);
    var viewport = qs('.tst-viewport', rootEl);
    var nav = qs('.tst-nav', rootEl);
    var dotsWrap = qs('.tst-dots', rootEl);
    var prevBtn = qs('.tst-prev', rootEl);
    var nextBtn = qs('.tst-next', rootEl);
    var toggleBtn = qs('.tst-toggle', rootEl);
    var refreshBtn = qs('.tst-refresh', rootEl);
    var statusEl = qs('.tst-status', rootEl);
    var template = qs('.tst-template', rootEl);
    var refreshUrl = rootEl.dataset.refreshUrl || '';

    var slides = qsa('.tst-slide', rootEl);
    if (slides.length < 2 && !refreshUrl) return;
    rootEl.dataset.tstReady = '1';

    var interval = parseInt(rootEl.dataset.interval, 10) || 6500;
    var DURATION = reduced ? 0 : 400;
    var current = 0, settleTimer = null, playTimer = null, statusTimer = null;
    var hovering = false, keyboard = false, inView = true, userPaused = false, loading = false;

    function getDots() { return qsa('.tst-dot', rootEl); }

    function finish() {
      if (settleTimer) { clearTimeout(settleTimer); settleTimer = null; }
      slides.forEach(function (s) { s.style.visibility = ''; });
    }

    // dir: 1 = next (enters from the right), -1 = previous (enters from the left)
    function show(index, dir) {
      if (index === current) return;
      finish();
      var from = slides[current], to = slides[index];

      to.classList.add('tst-instant');
      to.classList.toggle('is-prev', dir < 0);
      to.style.visibility = 'visible';
      void to.offsetWidth;
      to.classList.remove('tst-instant');

      from.style.visibility = 'visible';
      from.classList.remove('is-active');
      from.classList.toggle('is-prev', dir > 0);
      from.setAttribute('aria-hidden', 'true');

      to.classList.remove('is-prev');
      to.classList.add('is-active');
      to.removeAttribute('aria-hidden');

      current = index;
      updateDots();
      settleTimer = setTimeout(finish, DURATION + 30);
    }
    function step(dir) { if (slides.length > 1) show((current + dir + slides.length) % slides.length, dir); }
    function updateDots() {
      getDots().forEach(function (dot, i) { dot.setAttribute('aria-current', i === current ? 'true' : 'false'); });
    }

    // Autoplay: pauses on hover, keyboard focus, hidden tab, off screen, reduced motion, or the pause button
    function shouldPlay() { return !reduced && !userPaused && !hovering && !keyboard && inView && !loading && !document.hidden && slides.length > 1; }
    function schedule() {
      if (playTimer) { clearTimeout(playTimer); playTimer = null; }
      stage.setAttribute('aria-live', shouldPlay() ? 'off' : 'polite');
      if (!shouldPlay()) return;
      playTimer = setTimeout(function () { step(1); schedule(); }, interval);
    }
    function manual(dir) { step(dir); schedule(); }

    // Reload from the server
    function showStatus(msg) {
      if (!statusEl) return;
      statusEl.textContent = msg; statusEl.hidden = false;
      clearTimeout(statusTimer);
      statusTimer = setTimeout(hideStatus, 6000);
    }
    function hideStatus() { clearTimeout(statusTimer); if (!statusEl) return; statusEl.hidden = true; statusEl.textContent = ''; }
    function setLoading(on) {
      loading = on;
      refreshBtn.disabled = on;
      refreshBtn.setAttribute('aria-busy', on ? 'true' : 'false');
      refreshBtn.setAttribute('aria-label', on ? 'Loading new testimonials' : 'Show different testimonials');
      qs('.tst-icon-refresh', refreshBtn).classList.toggle('hidden', on);
      qs('.tst-icon-loading', refreshBtn).classList.toggle('hidden', !on);
    }
    function cleanList(data) {
      var list = data && Array.isArray(data.testimonials) ? data.testimonials : [];
      return list.filter(function (t) { return t && typeof t.quote === 'string' && t.quote.trim() !== ''; });
    }
    function fillQuote(el, text) {
      el.textContent = '';
      text.split(/\r\n|\r|\n/).forEach(function (line, i) {
        if (i > 0) el.appendChild(document.createElement('br'));
        el.appendChild(document.createTextNode(line));
      });
    }
    function buildSlide(t, index, total) {
      var el = template.content.firstElementChild.cloneNode(true);
      var name = typeof t.name === 'string' ? t.name.trim() : '';
      var title = typeof t.title === 'string' ? t.title.trim() : '';
      el.setAttribute('aria-label', (index + 1) + ' of ' + total);
      if (index === 0) el.classList.add('is-active'); else el.setAttribute('aria-hidden', 'true');
      fillQuote(qs('[data-tst-quote]', el), t.quote.trim());
      var initial = qs('[data-tst-initial]', el), anon = qs('[data-tst-anon]', el);
      if (name) { initial.textContent = name.charAt(0).toUpperCase(); anon.remove(); } else { initial.remove(); }
      qs('[data-tst-name]', el).textContent = name || 'Anonymous';
      var titleEl = qs('[data-tst-title]', el);
      if (title) titleEl.textContent = title; else titleEl.remove();
      return el;
    }
    function buildDots() {
      dotsWrap.textContent = '';
      slides.forEach(function (s, i) {
        var dot = document.createElement('button'), bar = document.createElement('span');
        dot.type = 'button'; dot.className = 'tst-dot';
        dot.setAttribute('aria-label', 'Go to testimonial ' + (i + 1));
        dot.setAttribute('aria-current', i === 0 ? 'true' : 'false');
        bar.className = 'tst-dot-bar';
        dot.appendChild(bar); dotsWrap.appendChild(dot);
      });
    }
    function replaceTestimonials(list) {
      finish();
      var frag = document.createDocumentFragment();
      list.forEach(function (t, i) { frag.appendChild(buildSlide(t, i, list.length)); });
      stage.textContent = ''; stage.appendChild(frag);
      slides = qsa('.tst-slide', stage);
      current = 0;
      buildDots();
      nav.hidden = slides.length < 2;
    }
    function swapWithFade(list) {
      return new Promise(function (resolve) {
        if (reduced) { replaceTestimonials(list); resolve(); return; }
        viewport.classList.add('is-swapping');
        setTimeout(function () { replaceTestimonials(list); viewport.classList.remove('is-swapping'); resolve(); }, 260);
      });
    }
    function refresh() {
      if (loading || !refreshUrl) return;
      var hadFocus = document.activeElement === refreshBtn;
      var controller = 'AbortController' in window ? new AbortController() : null;
      var timeout = setTimeout(function () { if (controller) controller.abort(); }, 15000);
      hideStatus(); setLoading(true); schedule();
      fetch(refreshUrl, { method: 'GET', credentials: 'same-origin', headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }, signal: controller ? controller.signal : undefined })
        .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(function (data) { var list = cleanList(data); if (!list.length) throw new Error('empty'); return swapWithFade(list); })
        .catch(function () { showStatus('Couldn\u2019t load new testimonials. Check your connection and try again.'); })
        .then(function () { clearTimeout(timeout); setLoading(false); if (hadFocus) refreshBtn.focus(); schedule(); });
    }

    // Controls
    if (prevBtn) prevBtn.addEventListener('click', function () { manual(-1); });
    if (nextBtn) nextBtn.addEventListener('click', function () { manual(1); });
    if (dotsWrap) dotsWrap.addEventListener('click', function (e) {
      var dot = e.target.closest('.tst-dot'); if (!dot) return;
      var i = getDots().indexOf(dot);
      if (i < 0 || i === current) return;
      show(i, i > current ? 1 : -1); schedule();
    });
    if (toggleBtn) toggleBtn.addEventListener('click', function () {
      userPaused = !userPaused;
      toggleBtn.setAttribute('aria-label', userPaused ? 'Start automatic sliding' : 'Pause automatic sliding');
      toggleBtn.setAttribute('aria-pressed', userPaused ? 'true' : 'false');
      qs('.tst-icon-pause', toggleBtn).classList.toggle('hidden', userPaused);
      qs('.tst-icon-play', toggleBtn).classList.toggle('hidden', !userPaused);
      schedule();
    });
    if (refreshBtn && template) refreshBtn.addEventListener('click', refresh);

    rootEl.addEventListener('mouseenter', function () { hovering = true; schedule(); });
    rootEl.addEventListener('mouseleave', function () { hovering = false; schedule(); });
    rootEl.addEventListener('focusin', function () { keyboard = true; schedule(); });
    rootEl.addEventListener('focusout', function (e) { if (rootEl.contains(e.relatedTarget)) return; keyboard = false; schedule(); });
    rootEl.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') { e.preventDefault(); manual(-1); }
      if (e.key === 'ArrowRight') { e.preventDefault(); manual(1); }
    });

    var startX = null;
    viewport.addEventListener('pointerdown', function (e) { startX = e.clientX; });
    viewport.addEventListener('pointerup', function (e) {
      if (startX === null) return;
      var dx = e.clientX - startX; startX = null;
      if (Math.abs(dx) > 50) manual(dx < 0 ? 1 : -1);
    });
    viewport.addEventListener('pointercancel', function () { startX = null; });

    document.addEventListener('visibilitychange', schedule);
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (en) { inView = en[0].isIntersecting; schedule(); }, { threshold: 0.35 }).observe(rootEl);
    }
    schedule();
  }
  qsa('[data-tst-slider]').forEach(initSlider);
})();


/* ---------------------------------------------------------------
   Services search.
   Hooks (data attributes, no ids): [data-service-search] wrapper (starts
   hidden), [data-service-search-input], [data-service-search-clear],
   [data-service-count] (data-total), [data-service-card] (data-title,
   data-blurb), [data-service-none], [data-service-clear-all].
   Without JS the search stays hidden and every card stays visible.
---------------------------------------------------------------- */
(function () {
  function initServiceSearch() {
    var wrap = document.querySelector('[data-service-search]');
    var input = document.querySelector('[data-service-search-input]');
    if (!wrap || !input) return; // search only renders with more than 3 services

    var clearBtn = document.querySelector('[data-service-search-clear]');
    var countEl = document.querySelector('[data-service-count]');
    var none = document.querySelector('[data-service-none]');
    var cards = document.querySelectorAll('[data-service-card]');
    var clearAll = document.querySelector('[data-service-clear-all]');

    wrap.classList.remove('hidden');
    wrap.classList.add('flex');

    function setClearVisible(on) {
      if (!clearBtn) return;
      clearBtn.classList.toggle('hidden', !on);
      clearBtn.classList.toggle('flex', on);
    }

    function applyFilter() {
      var terms = input.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
      var visible = 0;

      cards.forEach(function (card) {
        var haystack = ((card.dataset.title || '') + ' ' + (card.dataset.blurb || '')).toLowerCase();
        var match = terms.every(function (t) { return haystack.indexOf(t) !== -1; });
        card.classList.toggle('hidden', !match);
        if (match) visible += 1;
      });

      setClearVisible(terms.length > 0);
      if (none) none.classList.toggle('hidden', !(terms.length && visible === 0));

      if (countEl) {
        var total = parseInt(countEl.dataset.total, 10) || cards.length;
        countEl.textContent = terms.length
          ? 'Showing ' + visible + ' of ' + total
          : total + (total === 1 ? ' service' : ' services');
      }
    }

    function reset() {
      input.value = '';
      applyFilter();
      input.focus();
    }

    input.addEventListener('input', applyFilter);
    if (clearBtn) clearBtn.addEventListener('click', reset);
    if (clearAll) clearAll.addEventListener('click', reset);
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && input.value) { e.preventDefault(); reset(); }
    });
    applyFilter(); // handles browser-restored input values
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initServiceSearch);
  else initServiceSearch();
})();


/* ---------------------------------------------------------------
   Testimonials page: load more + share form.
   Hooks are data attributes (see the partials). Pages without these
   elements are unaffected: both init functions return early.
---------------------------------------------------------------- */
(function () {

  /* ============ Load more ============ */
  function initTestimonialsMore() {
    var grid = document.querySelector('[data-tst-grid]');
    var btn = document.querySelector('[data-tst-more]');
    if (!grid || !btn) return; // nothing more to load

    var wrap = document.querySelector('[data-tst-more-wrap]');
    var label = btn.querySelector('[data-tst-more-label]');
    var errorEl = document.querySelector('[data-tst-more-error]');
    var errorText = errorEl && errorEl.querySelector('[data-tst-more-error-text]');
    var statusEl = document.querySelector('[data-tst-more-status]');
    var skeletonTpl = document.querySelector('template[data-tst-skeleton]');

    var PLACEHOLDER = '123456789'; // the number the url tag was rendered with
    var batchPoint = btn.dataset.batchPoint;
    var loading = false;
    var skeletons = [];

    function urlFor(point) {
      return btn.dataset.urlTemplate.replace(PLACEHOLDER, encodeURIComponent(point));
    }

    function setLoading(on, retry) {
      loading = on;
      btn.disabled = on;
      if (on) btn.setAttribute('aria-busy', 'true'); else btn.removeAttribute('aria-busy');
      if (label) label.textContent = retry ? 'Try again' : 'Load more testimonials';
    }

    function addSkeletons() {
      if (!skeletonTpl || !skeletonTpl.content.firstElementChild) return;
      for (var i = 0; i < 3; i++) {
        var node = skeletonTpl.content.firstElementChild.cloneNode(true);
        grid.appendChild(node);
        skeletons.push(node);
      }
    }

    function removeSkeletons() {
      skeletons.forEach(function (node) { node.remove(); });
      skeletons = [];
    }

    function showError() {
      if (errorText) errorText.textContent = 'Couldn\u2019t load more testimonials. Check your connection and try again.';
      if (errorEl) errorEl.hidden = false;
    }

    btn.addEventListener('click', function () {
      if (loading) return;
      if (errorEl) errorEl.hidden = true;
      setLoading(true);
      addSkeletons();
      if (statusEl) statusEl.textContent = 'Loading more testimonials.';

      var controller = new AbortController();
      var timer = setTimeout(function () { controller.abort(); }, 15000);

      fetch(urlFor(batchPoint), {
        credentials: 'same-origin',
        headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        signal: controller.signal
      })
        .then(function (response) {
          return response.json().then(
            function (data) { return { ok: response.ok, data: data }; },
            function () { return { ok: response.ok, data: null }; }
          );
        })
        .then(function (result) {
          var data = result.data;
          if (!result.ok || !data || typeof data.html !== 'string') throw new Error('Unexpected response');

          // Cards arrive already rendered (same _cards.html partial as the page).
          // They are parsed in a detached <template>, marked as new, then moved into the grid.
          var holder = document.createElement('template');
          holder.innerHTML = data.html;
          var cards = Array.prototype.slice.call(holder.content.querySelectorAll('.tst-card'));

          removeSkeletons();
          var firstNew = null;
          cards.forEach(function (card) {
            card.classList.add('tst-card-new');
            card.setAttribute('tabindex', '-1'); // so the first new card can take focus
            if (!firstNew) firstNew = card;
            grid.appendChild(card);
          });

          // 0 is a valid batch point, so test for null/undefined, not truthiness
          var more = data.has_more === true && data.next_batch_point !== null && data.next_batch_point !== undefined;
          var count = cards.length;
          if (statusEl) {
            statusEl.textContent = count + (count === 1 ? ' more testimonial loaded' : ' more testimonials loaded') + (more ? '.' : '. That is all of them.');
          }

          if (more) {
            batchPoint = data.next_batch_point;
            setLoading(false);
          } else {
            // Nothing left: remove the button and keep keyboard users in place
            if (wrap) wrap.remove();
            if (firstNew) firstNew.focus({ preventScroll: true });
          }
        })
        .catch(function () {
          removeSkeletons();
          showError();
          setLoading(false, true);
          if (statusEl) statusEl.textContent = '';
        })
        .finally(function () { clearTimeout(timer); });
    });
  }

  /* ============ Share form ============ */
  function initShareForm() {
    var form = document.querySelector('[data-share-form]');
    if (!form) return;

    var anon = form.querySelector('[data-share-anon]');
    var identity = form.querySelector('[data-share-identity]');
    var nameInput = form.querySelector('[name="name"]');
    var titleInput = form.querySelector('[name="title"]');
    var quoteInput = form.querySelector('[name="quote"]');
    var banner = form.querySelector('[data-share-banner]');
    var bannerText = banner && banner.querySelector('[data-share-banner-text]');
    var submitBtn = form.querySelector('[data-share-submit]');
    var successEl = document.querySelector('[data-share-success]');
    var anotherBtn = document.querySelector('[data-share-another]');

    // ---- Per-field messages. The error replaces the helper text (if the field has one). ----

    function fieldWrap(name) {
      var wraps = form.querySelectorAll('[data-field]');
      for (var i = 0; i < wraps.length; i++) if (wraps[i].dataset.field === name) return wraps[i];
      return null;
    }

    function setFieldError(name, message) {
      var wrap = fieldWrap(name);
      if (!wrap) return false;
      var control = wrap.querySelector('input, select, textarea');
      var err = wrap.querySelector('[data-field-error]');
      var text = wrap.querySelector('[data-field-error-text]');
      if (!control || !err || !text || control.offsetParent === null) return false; // missing or hidden (anonymous)
      var hint = wrap.querySelector('[data-field-hint]');
      text.textContent = message; // textContent, never innerHTML
      err.hidden = false;
      if (hint) hint.hidden = true;
      if (!err.id) err.id = 'err-' + name;
      if (control.dataset.describedby === undefined) control.dataset.describedby = control.getAttribute('aria-describedby') || '';
      control.setAttribute('aria-invalid', 'true');
      control.setAttribute('aria-describedby', err.id);
      return true;
    }

    function clearFieldError(name) {
      var wrap = fieldWrap(name);
      if (!wrap) return;
      var control = wrap.querySelector('input, select, textarea');
      var err = wrap.querySelector('[data-field-error]');
      var hint = wrap.querySelector('[data-field-hint]');
      if (err) err.hidden = true;
      if (hint) hint.hidden = false;
      if (control) {
        control.removeAttribute('aria-invalid');
        // Restore the helper text link (if the field had one)
        if (control.dataset.describedby) control.setAttribute('aria-describedby', control.dataset.describedby);
        else control.removeAttribute('aria-describedby');
      }
    }

    function showBanner(message) {
      if (!banner || !bannerText) return;
      bannerText.textContent = message;
      banner.hidden = false;
    }

    function clearAll() {
      ['name', 'title', 'service', 'quote'].forEach(clearFieldError);
      if (banner) banner.hidden = true;
    }

    // ---- Quick checks (the server checks again) ----

    function message(name) {
      if (name === 'name' && !anon.checked && !nameInput.value.trim()) return 'Enter your name, or switch on Stay anonymous.';
      if (name === 'quote' && !quoteInput.value.trim()) return 'Write your testimonial before you submit.';
      return '';
    }

    // Validate on blur, then re-check on every change once a field has been flagged
    [['name', nameInput], ['quote', quoteInput]].forEach(function (pair) {
      var name = pair[0], control = pair[1];
      if (!control) return;
      control.addEventListener('blur', function () {
        var m = message(name);
        if (m) setFieldError(name, m); else clearFieldError(name);
      });
      control.addEventListener('input', function () {
        if (control.getAttribute('aria-invalid') === 'true' && !message(name)) clearFieldError(name);
      });
    });

    // ---- Stay anonymous ----
    // On: hide name and title and clear them (they post blank, so the server stores null).
    // What was typed is remembered, so switching back off does not lose it.

    function applyAnonymous() {
      if (anon.checked) {
        if (nameInput.value || titleInput.value) {
          identity.dataset.stashName = nameInput.value;
          identity.dataset.stashTitle = titleInput.value;
        }
        nameInput.value = '';
        titleInput.value = '';
        clearFieldError('name');
        clearFieldError('title');
        identity.hidden = true;
      } else {
        if (!nameInput.value && !titleInput.value) {
          nameInput.value = identity.dataset.stashName || '';
          titleInput.value = identity.dataset.stashTitle || '';
        }
        identity.hidden = false;
      }
    }

    anon.addEventListener('change', applyAnonymous);
    applyAnonymous();

    // ---- Server errors ----
    // errors looks like { quote: ["This field is required."], __all__: ["..."] }

    function firstMessage(value) {
      var first = Array.isArray(value) ? value[0] : value;
      return typeof first === 'string' ? first : (first && first.message) || 'That value isn\u2019t valid.';
    }

    function showServerErrors(errors) {
      var placed = false;
      Object.keys(errors).forEach(function (key) {
        var m = firstMessage(errors[key]);
        if (key !== '__all__' && setFieldError(key, m)) placed = true;
        else if (banner && banner.hidden) showBanner(m); // non-field error, or the field is hidden
      });
      return placed;
    }

    function setBusy(busy) {
      submitBtn.disabled = busy;
      if (busy) submitBtn.setAttribute('aria-busy', 'true'); else submitBtn.removeAttribute('aria-busy');
    }

    // ---- Submit ----

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      clearAll();

      // Check in page order and focus the first problem
      var firstBad = null;
      [['name', nameInput], ['quote', quoteInput]].forEach(function (pair) {
        var m = message(pair[0]);
        if (m && setFieldError(pair[0], m) && !firstBad) firstBad = pair[1];
      });
      if (firstBad) { firstBad.focus(); return; }

      setBusy(true);

      var controller = new AbortController();
      var timer = setTimeout(function () { controller.abort(); }, 15000);

      fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },
        signal: controller.signal
      })
        .then(function (response) {
          return response.json().then(
            function (data) { return { response: response, data: data }; },
            function () { return { response: response, data: null }; }
          );
        })
        .then(function (result) {
          var data = result.data;
          if (result.response.ok && data && data.ok !== false) { showSuccess(); return; }
          if (!data) { showBanner('Something went wrong on our side. Try again in a moment.'); return; }
          var placed = data.errors ? showServerErrors(data.errors) : false;
          if (data.message) showBanner(data.message);
          else if (!placed && banner && banner.hidden) showBanner('Couldn\u2019t send your testimonial. Check what you entered and try again.');
          // Preserve input; focus the first flagged field
          var bad = form.querySelector('[aria-invalid="true"]');
          if (bad) bad.focus();
        })
        .catch(function (error) {
          showBanner(error && error.name === 'AbortError'
            ? 'This is taking too long. Check your connection and try again.'
            : 'Couldn\u2019t reach the server. Check your connection and try again.');
        })
        .finally(function () {
          clearTimeout(timer);
          setBusy(false);
        });
    });

    // ---- Success / share another ----

    function showSuccess() {
      // Umami custom event: the testimonial was saved. Guarded so a blocked tracker can't break the form.
      try { if (window.umami) window.umami.track('testimonial-form-success'); } catch (e) {}
      form.hidden = true;
      successEl.hidden = false;
      successEl.focus();
    }

    if (anotherBtn) {
      anotherBtn.addEventListener('click', function () {
        form.reset();
        delete identity.dataset.stashName;
        delete identity.dataset.stashTitle;
        clearAll();
        applyAnonymous();
        successEl.hidden = true;
        form.hidden = false;
        (anon.checked ? quoteInput : nameInput).focus();
      });
    }
  }

  function init() { initTestimonialsMore(); initShareForm(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();


/* Busy buttons. Same behavior as static/js/staffs.js, for pages that load ui.js (public and dashboard).
   Markup contract (components/_button.html produces it):
     <form data-busy-form> ... <button type="submit" data-busy-label="Sending"><svg data-btn-spinner class="hidden">...</svg><span data-btn-label>Send</span></button>
     <a|button data-busy-click data-busy-label="Resending">  (link or non-submit button that disables itself when clicked)
   Submit buttons lock on submit (after the page's own validation passes), not on click, so a failed check never leaves them stuck.
   Guarded so it binds once even if staffs.js is also on the page. */
(function () {
  'use strict';
  if (window.__staffsBusyBound) return;
  window.__staffsBusyBound = true;

  function setBusy(btn, busy, keepDisabled) {
    if (!btn) return;
    var label = btn.querySelector('[data-btn-label]');
    var spinner = btn.querySelector('[data-btn-spinner]');
    var isLink = btn.tagName === 'A';
    if (label && btn.getAttribute('data-idle-label') === null) btn.setAttribute('data-idle-label', label.textContent);
    var busyLabel = btn.getAttribute('data-busy-label');
    if (busy) {
      btn.setAttribute('aria-busy', 'true');
      btn.setAttribute('data-busy', 'true');
      if (isLink) { btn.setAttribute('aria-disabled', 'true'); btn.setAttribute('tabindex', '-1'); } else { btn.disabled = true; }
      if (spinner) spinner.classList.remove('hidden');
      if (label && busyLabel) label.textContent = busyLabel;
    } else {
      btn.removeAttribute('aria-busy');
      btn.removeAttribute('data-busy');
      if (isLink) { btn.removeAttribute('aria-disabled'); btn.removeAttribute('tabindex'); } else { btn.disabled = !!keepDisabled; }
      if (spinner) spinner.classList.add('hidden');
      if (label && btn.getAttribute('data-idle-label') !== null) label.textContent = btn.getAttribute('data-idle-label');
    }
  }
  window.setButtonBusy = window.setButtonBusy || setBusy;

  document.addEventListener('submit', function (e) {
    var form = e.target;
    if (!form || !form.hasAttribute || !form.hasAttribute('data-busy-form') || e.defaultPrevented) return;
    if (form.getAttribute('data-submitting') === 'true') { e.preventDefault(); return; }
    form.setAttribute('data-submitting', 'true');
    setBusy(e.submitter || form.querySelector('[type="submit"]'), true);
  });

  document.addEventListener('click', function (e) {
    var el = e.target.closest ? e.target.closest('[data-busy-click]') : null;
    if (!el) return;
    if (el.getAttribute('data-busy') === 'true') { e.preventDefault(); return; }
    if (el.type === 'submit') return;
    setBusy(el, true);
  });

  window.addEventListener('pageshow', function (e) {
    if (!e.persisted) return;
    Array.prototype.forEach.call(document.querySelectorAll('[data-submitting]'), function (f) { f.removeAttribute('data-submitting'); });
    Array.prototype.forEach.call(document.querySelectorAll('[data-busy="true"]'), function (b) { setBusy(b, false); });
  });
})();