/*
 * Dashboard behavior. Loaded by templates/base/dashboard/base.html (not deferred).
 * Replaces the inline scripts of _sidebar, _topbar, _toast and _form_helpers for dashboard pages.
 * Public globals kept for the other dashboard pages:
 *   showToast, queueToast, ajaxPost, submitForm, clearFieldErrors, autoUploadImage
 * Component styles (.sb-*, .dash-pop*, .app-toast*, .field-*) live in input.css.
 */
(function () {
  'use strict';

  var root = document.documentElement;
  function $(id) { return document.getElementById(id); }

  /* ------------------------------------------------------------------ */
  /* 1. Theme: light, dark or system (same storage key as the public site) */
  /* ------------------------------------------------------------------ */
  var darkQuery = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

  function storedTheme() {
    try {
      var v = localStorage.getItem('theme');
      if (v === 'light' || v === 'dark') return v;
    } catch (e) { /* storage unavailable */ }
    return 'system';
  }

  function applyTheme(pref) {
    var dark = pref === 'system' ? !!(darkQuery && darkQuery.matches) : pref === 'dark';
    var theme = dark ? 'dark' : 'light';
    root.setAttribute('data-theme', theme);
    root.setAttribute('data-theme-pref', pref);
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', meta.getAttribute('data-' + theme));
    document.querySelectorAll('[data-theme-option]').forEach(function (btn) {
      btn.setAttribute('aria-pressed', btn.getAttribute('data-theme-option') === pref ? 'true' : 'false');
    });
  }

  function setTheme(pref) {
    try {
      if (pref === 'system') localStorage.removeItem('theme');
      else localStorage.setItem('theme', pref);
    } catch (e) { /* the choice still applies for this page */ }
    applyTheme(pref);
  }

  document.querySelectorAll('[data-theme-option]').forEach(function (btn) {
    btn.addEventListener('click', function () { setTheme(btn.getAttribute('data-theme-option')); });
  });
  if (darkQuery && darkQuery.addEventListener) {
    darkQuery.addEventListener('change', function () { if (storedTheme() === 'system') applyTheme('system'); });
  }
  window.addEventListener('storage', function (e) { if (e.key === 'theme') applyTheme(storedTheme()); });
  applyTheme(storedTheme());

  /* ------------------------------------------------------------------ */
  /* 2. Popover menus (theme menu, account menu)                          */
  /* ------------------------------------------------------------------ */
  var pops = [];

  function bindPopover(btn, menu) {
    if (!btn || !menu) return;
    var api = { btn: btn, menu: menu };

    api.close = function (returnFocus) {
      if (menu.hidden) return;
      menu.hidden = true;
      btn.setAttribute('aria-expanded', 'false');
      if (returnFocus) btn.focus();
    };
    api.open = function () {
      pops.forEach(function (p) { if (p !== api) p.close(false); });
      menu.hidden = false;
      btn.setAttribute('aria-expanded', 'true');
    };

    btn.addEventListener('click', function () { if (menu.hidden) api.open(); else api.close(false); });
    btn.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowDown') return;
      e.preventDefault();
      api.open();
      var first = menu.querySelector('a, button');
      if (first) first.focus();
    });
    menu.addEventListener('focusout', function (e) {
      var to = e.relatedTarget;
      if (to && !menu.contains(to) && to !== btn) api.close(false);
    });
    pops.push(api);
  }

  bindPopover($('themeBtn'), $('themeMenu'));
  bindPopover($('userMenuBtn'), $('userMenu'));

  document.addEventListener('click', function (e) {
    pops.forEach(function (p) {
      if (!p.menu.hidden && !p.menu.contains(e.target) && !p.btn.contains(e.target)) p.close(false);
    });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    pops.forEach(function (p) { p.close(true); });
  });

  /* ------------------------------------------------------------------ */
  /* 3. Log out confirmation (native dialog)                              */
  /* ------------------------------------------------------------------ */
  (function () {
    var dlg = $('logoutDialog');
    var trigger = $('openLogoutModal');
    var cancel = $('cancelLogoutModal');
    var menuBtn = $('userMenuBtn');
    if (!dlg || !trigger || typeof dlg.showModal !== 'function') return; // the link then logs out directly

    trigger.addEventListener('click', function (e) {
      e.preventDefault();
      pops.forEach(function (p) { p.close(false); });
      dlg.showModal();
    });
    if (cancel) cancel.addEventListener('click', function () { dlg.close(); });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); }); // click on the backdrop
    dlg.addEventListener('close', function () { if (menuBtn) menuBtn.focus(); });
  })();

  /* ------------------------------------------------------------------ */
  /* 4. Sidebar: retractable on desktop, drawer on mobile                 */
  /* ------------------------------------------------------------------ */
  (function () {
    var sidebar = $('sidebar');
    if (!sidebar) return;

    var openBtn = $('sidebarToggleBtn');
    var closeBtn = $('sidebarCloseBtn');
    var backdrop = $('sidebarBackdrop');
    var collapseBtn = $('sidebarCollapseBtn');
    var nav = $('sidebarNav');
    var tip = $('sidebarTip');
    var desktop = window.matchMedia('(min-width: 1024px)');
    var drawerOpen = false;

    /* ---- Mobile drawer ---- */
    // Off-canvas links must not be reachable by keyboard or screen reader
    function syncInert() { sidebar.inert = !desktop.matches && !drawerOpen; }

    function setDrawer(open, returnFocus) {
      drawerOpen = open;
      sidebar.classList.toggle('-translate-x-full', !open);
      backdrop.hidden = !open;
      if (openBtn) openBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      syncInert();
      if (open && closeBtn) closeBtn.focus();
      if (!open && returnFocus && openBtn) openBtn.focus();
    }

    if (openBtn) openBtn.addEventListener('click', function () { setDrawer(true); });
    if (closeBtn) closeBtn.addEventListener('click', function () { setDrawer(false, true); });
    backdrop.addEventListener('click', function () { setDrawer(false, true); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && drawerOpen) setDrawer(false, true);
    });
    var onBreakpoint = function () { if (desktop.matches) setDrawer(false, false); else syncInert(); hideTip(); };
    if (desktop.addEventListener) desktop.addEventListener('change', onBreakpoint);

    /* ---- Retract and expand (desktop) ---- */
    function isCollapsed() { return root.getAttribute('data-sidebar') === 'collapsed'; }

    function syncCollapseLabel() {
      if (!collapseBtn) return;
      var label = collapseBtn.querySelector('.sb-label');
      if (label) label.textContent = isCollapsed() ? 'Expand sidebar' : 'Collapse sidebar';
    }

    function setCollapsed(collapsed) {
      if (collapsed) root.setAttribute('data-sidebar', 'collapsed');
      else root.removeAttribute('data-sidebar');
      try { localStorage.setItem('dashboard-sidebar', collapsed ? 'collapsed' : 'expanded'); } catch (e) { /* not remembered */ }
      syncCollapseLabel();
      hideTip();
    }

    if (collapseBtn) {
      collapseBtn.addEventListener('click', function () {
        setCollapsed(!isCollapsed());
        showTip(collapseBtn); // the pointer is still over the button, so show its new name
      });
    }

    /* ---- Tooltip for the icon rail ---- */
    function hideTip() { if (tip) tip.hidden = true; }

    function tipText(item) {
      var label = item.querySelector('.sb-label');
      var text = label ? label.textContent.trim() : '';
      var badge = item.querySelector('.sb-badge');
      if (badge && window.getComputedStyle(badge).display !== 'none' && badge.textContent.trim()) {
        text += ' (' + badge.textContent.trim() + ')';
      }
      return text;
    }

    function showTip(item) {
      if (!tip || !desktop.matches || !isCollapsed()) return;
      var text = tipText(item);
      if (!text) return;
      var r = item.getBoundingClientRect();
      tip.textContent = text;
      tip.style.left = (r.right + 8) + 'px';
      tip.style.top = (r.top + r.height / 2) + 'px';
      tip.hidden = false;
    }

    sidebar.addEventListener('mouseover', function (e) {
      var item = e.target.closest('[data-sb-item]');
      if (item) showTip(item);
    });
    sidebar.addEventListener('mouseout', function (e) {
      var item = e.target.closest('[data-sb-item]');
      if (item && !item.contains(e.relatedTarget)) hideTip();
    });
    sidebar.addEventListener('focusin', function (e) {
      var item = e.target.closest('[data-sb-item]');
      if (item && item.matches(':focus-visible')) showTip(item);
    });
    sidebar.addEventListener('focusout', hideTip);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') hideTip(); });
    if (nav) nav.addEventListener('scroll', hideTip);

    syncCollapseLabel();
    syncInert();
  })();

  /* ------------------------------------------------------------------ */
  /* 5. Toasts, fetch helpers and the shared form submit                  */
  /* ------------------------------------------------------------------ */
  var STORAGE_KEY = 'dashboardPendingToast';
  var DURATION_MS = { success: 5000, info: 5000, error: 8000 };
  var MAX_TOASTS = 4;
  var toastRoot = $('toastRoot');

  var ICONS = {
    success: '<path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/>',
    error: '<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z"/>',
    info: '<path stroke-linecap="round" stroke-linejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z"/>'
  };
  var X_MARK = '<path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12"/>';

  function svg(inner, size, cls) {
    return '<svg class="' + (cls || '') + '" width="' + size + '" height="' + size + '" fill="none" viewBox="0 0 24 24" ' +
      'stroke="currentColor" stroke-width="1.5" aria-hidden="true" focusable="false">' + inner + '</svg>';
  }

  window.showToast = function (message, type) {
    if (!toastRoot) return;
    type = ICONS[type] ? type : 'info';

    var toast = document.createElement('div');
    toast.className = 'app-toast app-toast--' + type;
    if (type === 'error') toast.setAttribute('role', 'alert');
    toast.innerHTML =
      svg(ICONS[type], 20, 'app-toast__icon') +
      '<p class="app-toast__msg"></p>' +
      '<button type="button" class="app-toast__close" aria-label="Dismiss notification">' + svg(X_MARK, 16, '') + '</button>';
    // textContent, never innerHTML, so server messages cannot inject markup
    toast.querySelector('.app-toast__msg').textContent = message;

    var timer = null;
    var remaining = DURATION_MS[type];
    var startedAt = 0;

    function close() {
      clearTimeout(timer);
      toast.setAttribute('data-leaving', '');
      setTimeout(function () { toast.remove(); }, 200);
    }
    function start() {
      if (timer !== null) return;
      startedAt = Date.now();
      timer = setTimeout(close, remaining);
    }
    // Timed messages pause while the pointer or keyboard focus is on them (WCAG 2.2.1)
    function pause() {
      if (timer === null) return;
      clearTimeout(timer);
      timer = null;
      remaining = Math.max(2000, remaining - (Date.now() - startedAt));
    }

    toast.querySelector('.app-toast__close').addEventListener('click', close);
    toast.addEventListener('mouseenter', pause);
    toast.addEventListener('mouseleave', start);
    toast.addEventListener('focusin', pause);
    toast.addEventListener('focusout', start);

    while (toastRoot.children.length >= MAX_TOASTS) toastRoot.firstElementChild.remove();
    toastRoot.appendChild(toast);
    start();
  };

  // Save a toast to show after the next page load (used before location.reload())
  window.queueToast = function (message, type) {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ message: message, type: type }));
    } catch (e) { /* storage unavailable: the toast is simply skipped */ }
  };

  // Show a toast queued by the previous page load, once
  try {
    var pending = sessionStorage.getItem(STORAGE_KEY);
    if (pending) {
      sessionStorage.removeItem(STORAGE_KEY);
      var queued = JSON.parse(pending);
      if (queued && queued.message) window.showToast(queued.message, queued.type);
    }
  } catch (e) { /* ignore */ }

  // Field errors from a JSON response. Reads `form_errors` (new) or `errors` (older views).
  // The value can be an object or a JSON string, for example form.errors.as_json().
  // Returns { field: [ "text" | { message } ] } or null.
  function parseFieldErrors(data) {
    var raw = data.form_errors || data.errors;
    if (typeof raw === 'string') {
      try { raw = JSON.parse(raw); } catch (e) { return null; }
    }
    return raw && typeof raw === 'object' ? raw : null;
  }

  // POST a form with fetch. Always resolves (never rejects) with { ok, status, data, message, fieldErrors }.
  // `message` is the server's message, or a friendly one for timeouts, network errors,
  // expired sessions and non-JSON responses.
  window.ajaxPost = function (form, options) {
    var timeoutMs = (options && options.timeoutMs) || 15000;
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, timeoutMs);

    return fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },
      credentials: 'same-origin',
      signal: controller.signal
    })
      .then(function (response) {
        return response.json().then(
          function (data) { return { response: response, data: data }; },
          function () { return { response: response, data: null }; }
        );
      })
      .then(function (r) {
        var response = r.response;
        var data = r.data;

        if (data && typeof data === 'object') {
          var serverError = typeof data.error === 'string' ? data.error : '';
          var ok = response.ok && data.ok !== false && !serverError;
          return {
            ok: ok,
            status: response.status,
            data: data,
            fieldErrors: parseFieldErrors(data),
            message: data.message || serverError || (ok ? '' : 'Something went wrong. Try again.')
          };
        }

        // Not JSON: usually a redirect to the login page, or a server error page
        return {
          ok: false,
          status: response.status,
          data: null,
          message: response.redirected
            ? 'Your session may have expired. Refresh the page and log in again.'
            : 'Unexpected response from the server (' + response.status + '). Try again.'
        };
      })
      .catch(function (error) {
        var timedOut = !!error && error.name === 'AbortError';
        return {
          ok: false,
          status: 0,
          data: null,
          timedOut: timedOut,
          message: timedOut
            ? 'The request timed out. Try again.'
            : 'Could not reach the server. Check your connection and try again.'
        };
      })
      .finally(function () { clearTimeout(timer); });
  };

  /* ---- Field errors ---- */
  function isControl(el) { return el.matches && el.matches('input, select, textarea'); }

  function clearFieldErrors(form) {
    form.querySelectorAll('.field-error').forEach(function (el) { el.remove(); });
    form.querySelectorAll('[data-has-error]').forEach(function (el) {
      el.removeAttribute('data-has-error');
      el.removeAttribute('aria-invalid');
      if (el.hasAttribute('data-orig-describedby')) {
        var orig = el.getAttribute('data-orig-describedby');
        if (orig) el.setAttribute('aria-describedby', orig); else el.removeAttribute('aria-describedby');
        el.removeAttribute('data-orig-describedby');
      }
    });
  }

  // errors looks like { question: ["This field is required."], ... }
  // opts.fieldTarget(name, form) may return the element to put a field's error under
  // (for example the note under a file picker).
  function showFieldErrors(form, errors, opts) {
    var firstControl = null;

    Object.keys(errors).forEach(function (name) {
      var target = (opts && opts.fieldTarget && opts.fieldTarget(name, form)) ||
        form.querySelector('[name="' + name + '"]');
      if (!target) return; // for example non-field errors: the toast covers those

      var list = Array.isArray(errors[name]) ? errors[name] : [errors[name]];
      var first = list[0];
      var text = typeof first === 'string' ? first : (first && first.message) || 'This value is not valid.';

      var p = document.createElement('p');
      p.className = 'field-error';
      p.id = 'error-' + name;
      p.setAttribute('role', 'alert');
      p.innerHTML = svg(ICONS.error, 16, '') + '<span></span>';
      p.querySelector('span').textContent = text;
      target.insertAdjacentElement('afterend', p);

      target.setAttribute('data-has-error', '');
      if (isControl(target)) {
        target.setAttribute('aria-invalid', 'true');
        target.setAttribute('data-orig-describedby', target.getAttribute('aria-describedby') || '');
        target.setAttribute('aria-describedby', ((target.getAttribute('aria-describedby') || '') + ' ' + p.id).trim());
        if (!firstControl) firstControl = target;
      }
    });

    if (firstControl && !firstControl.hidden) firstControl.focus(); // focus the first error
  }

  window.clearFieldErrors = clearFieldErrors;

  // Posts `form` with fetch and reports the result with a toast.
  //   opts.button, opts.spinner, opts.label   the submit button parts (spinner and label optional)
  //   opts.busyText / opts.idleText           label while sending / at rest
  //   opts.successFallback                    toast text if the server sent none
  //   opts.onSuccess(result)                  optional. Without it the page reloads (the toast
  //                                           shows after the reload). With it, the page stays put.
  //   opts.fieldTarget(name, form)            optional, see showFieldErrors
  //   opts.timeoutMs                          optional, default 15000
  window.submitForm = function (form, opts) {
    clearFieldErrors(form);

    opts.button.disabled = true;
    opts.button.setAttribute('aria-busy', 'true');
    if (opts.spinner) opts.spinner.classList.remove('hidden');
    if (opts.label) opts.label.textContent = opts.busyText;

    function resetButton() {
      opts.button.disabled = false;
      opts.button.removeAttribute('aria-busy');
      if (opts.spinner) opts.spinner.classList.add('hidden');
      if (opts.label) opts.label.textContent = opts.idleText;
    }

    return window.ajaxPost(form, { timeoutMs: opts.timeoutMs }).then(function (result) {
      if (result.ok) {
        var text = result.message || opts.successFallback;
        if (opts.onSuccess) {
          resetButton();
          window.showToast(text, 'success');
          opts.onSuccess(result);
        } else {
          window.queueToast(text, 'success');
          window.location.reload();
        }
        return result;
      }

      resetButton();
      if (result.fieldErrors) showFieldErrors(form, result.fieldErrors, opts);
      window.showToast(result.message, 'error');
      return result;
    });
  };

  /* ------------------------------------------------------------------ */
  /* 6. Inline edit forms (.site-info-form) and image upload on choose    */
  /* ------------------------------------------------------------------ */
  // Edit, Cancel and Save are shown and hidden with opacity, so they keep their place in the layout.
  // `inert` makes the hidden ones unreachable by keyboard and screen reader. Pages that
  // use the older markup (without inert in the HTML) get the same behavior from this code.
  function setActionVisible(el, visible) {
    if (!el) return;
    el.classList.toggle('opacity-0', !visible);
    el.classList.toggle('pointer-events-none', !visible);
    el.inert = !visible;
  }

  function setEditing(form, editing) {
    form.querySelectorAll('.site-view-value').forEach(function (el) { el.classList.toggle('hidden', editing); });
    form.querySelectorAll('.site-edit-field').forEach(function (el) { el.classList.toggle('hidden', !editing); });

    setActionVisible(form.querySelector('[data-action="edit"]'), !editing);
    setActionVisible(form.querySelector('[data-action="save"]'), editing);
    setActionVisible(form.querySelector('[data-action="cancel"]'), editing);
  }

  function enterEditMode(form) {
    // Snapshot current values so Cancel can restore them later
    form.querySelectorAll('.site-edit-field').forEach(function (el) { el.dataset.originalValue = el.value; });
    clearFieldErrors(form);
    setEditing(form, true);
    var firstField = form.querySelector('.site-edit-field');
    if (firstField) firstField.focus();
  }

  // discard = true restores the snapshot (Cancel); false keeps what is in the fields (after a save)
  function exitEditMode(form, discard) {
    if (discard) {
      form.querySelectorAll('.site-edit-field').forEach(function (el) {
        if (el.dataset.originalValue !== undefined) el.value = el.dataset.originalValue;
      });
    }
    clearFieldErrors(form);
    setEditing(form, false);
    var editBtn = form.querySelector('[data-action="edit"]');
    if (editBtn) editBtn.focus();
  }

  // After a successful save: put the new values into the read-only text and leave edit mode.
  // If the view returns { "values": { "<field name>": "<text to show>" } } that text is used,
  // otherwise the value is shown exactly as it was typed (no case changes).
  function commitSave(form, result) {
    var values = (result.data && result.data.values) || {};

    form.querySelectorAll('.site-edit-field').forEach(function (field) {
      var view = field.parentElement.querySelector('.site-view-value');
      if (view) {
        var text = values[field.name] !== undefined ? values[field.name] : field.value;
        view.textContent = text || 'Not set';
        if (text) view.removeAttribute('data-empty'); else view.setAttribute('data-empty', '');
      }
      field.dataset.originalValue = field.value;
    });

    var lastUpdated = form.querySelector('[data-last-updated]');
    if (lastUpdated) {
      lastUpdated.textContent = form.dataset.justNow || '(Last updated: just now)';
      lastUpdated.hidden = false;
    }

    exitEditMode(form, false);
  }

  document.addEventListener('click', function (event) {
    var trigger = event.target.closest('[data-action="edit"], [data-action="cancel"]');
    if (!trigger) return;
    var form = trigger.closest('.site-info-form');
    if (!form) return;

    if (trigger.dataset.action === 'edit') enterEditMode(form);
    else exitEditMode(form, true);
  });

  document.addEventListener('keydown', function (event) {
    var form = event.target.closest && event.target.closest('.site-info-form');
    if (!form) return;

    // Older markup uses a div as the Edit trigger. Real buttons already handle Enter and Space.
    if ((event.key === 'Enter' || event.key === ' ') && event.target.matches('[data-action="edit"]') && event.target.tagName !== 'BUTTON') {
      event.preventDefault();
      enterEditMode(form);
      return;
    }

    // Esc leaves edit mode without saving
    if (event.key === 'Escape') {
      var cancelBtn = form.querySelector('[data-action="cancel"]');
      if (cancelBtn && !cancelBtn.inert) {
        event.preventDefault();
        exitEditMode(form, true);
      }
    }
  });

  // Save posts with fetch; the page stays where it is
  document.addEventListener('submit', function (event) {
    var form = event.target;
    if (!form.classList || !form.classList.contains('site-info-form')) return;

    event.preventDefault();
    var label = form.querySelector('[data-save-label]');
    window.submitForm(form, {
      button: form.querySelector('[data-action="save"]'),
      spinner: form.querySelector('[data-btn-spinner]'),
      label: label,
      busyText: 'Saving...',
      idleText: (label && label.textContent) || 'Save',
      successFallback: form.dataset.successMessage || 'Changes saved.',
      onSuccess: function (result) { commitSave(form, result); }
    });
  });

  // Image upload on file choose
  //   opts.input            the <input type="file"> (must sit inside the form to post)
  //   opts.img              the <img> to preview in
  //   opts.otherImages      optional CSS selector of more <img>s to update after a save
  //   opts.successFallback  toast text if the server sent none
  // The server may return { "url": "..." } to swap the preview for the saved file.
  window.autoUploadImage = function (opts) {
    var input = opts.input;
    var img = opts.img;
    if (!input || !img) return;
    var form = opts.form || input.form;

    input.addEventListener('change', function () {
      var file = input.files && input.files[0];
      if (!file) return;

      if (file.type && file.type.indexOf('image/') !== 0) {
        window.showToast('Choose an image file.', 'error');
        input.value = '';
        return;
      }

      var previous = img.src;
      img.src = URL.createObjectURL(file); // instant preview
      img.classList.add('opacity-60');

      window.ajaxPost(form).then(function (result) {
        img.classList.remove('opacity-60');

        if (result.ok) {
          var url = result.data && result.data.url;
          if (url) img.src = url;
          if (opts.otherImages) {
            document.querySelectorAll(opts.otherImages).forEach(function (other) { other.src = url || img.src; });
          }
          window.showToast(result.message || opts.successFallback || 'Image updated.', 'success');
        } else {
          img.src = previous; // put the old image back
          window.showToast(result.message, 'error');
        }

        input.value = ''; // lets the same file be chosen again
      });
    });
  };
})();

/* ==========================================================================
   Dashboard modal helper.
   Contents partials call dashModal.opened / closed after they show or hide a modal.
   Staffs and Reports use dashModal.open / close, which also handle Esc.
   It moves focus into the dialog, keeps Tab inside it, and returns focus to the opener.
   ========================================================================== */
(function () {
  var FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
  var openers = new WeakMap();

  function focusables(modal) {
    return Array.prototype.filter.call(modal.querySelectorAll(FOCUSABLE), function (el) {
      return el.offsetParent !== null;
    });
  }

  function trap(event) {
    if (event.key !== 'Tab') return;
    var items = focusables(event.currentTarget);
    if (!items.length) return;
    var first = items[0];
    var last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  var stack = []; // modals opened through dashModal.open, last one is on top (Esc closes it)

  function setShown(el, on, display) {
    el.classList.toggle('hidden', !on);
    if (display !== '') el.classList.toggle(display || 'flex', on);
  }

  window.dashModal = {
    stack: stack,
    setShown: setShown,
    // Full open/close for page scripts (Staffs, Reports): show + scroll lock + opened()/closed() + Esc.
    // opts: opener (gets focus back on close), focus (element to focus first), onRequestClose (called on Esc)
    open: function (el, opts) {
      opts = opts || {};
      setShown(el, true);
      document.body.classList.add('overflow-hidden');
      stack.push({ el: el, opener: opts.opener || null, close: opts.onRequestClose });
      this.opened(el);
      if (opts.focus) opts.focus.focus();
    },
    close: function (el) {
      var entry = null;
      for (var i = 0; i < stack.length; i++) if (stack[i].el === el) { entry = stack.splice(i, 1)[0]; break; }
      setShown(el, false);
      if (!stack.length) document.body.classList.remove('overflow-hidden');
      this.closed(el);
      if (entry && entry.opener && document.contains(entry.opener)) entry.opener.focus();
    },
    opened: function (modal) {
      if (!modal) return;
      openers.set(modal, document.activeElement);
      modal.addEventListener('keydown', trap);
      // Prefer the first form field over the Close button
      var target = modal.querySelector('input:not([type="hidden"]):not([type="checkbox"]):not([type="file"]), textarea, select') || focusables(modal)[0];
      if (target) target.focus();
    },
    closed: function (modal) {
      if (!modal) return;
      modal.removeEventListener('keydown', trap);
      var opener = openers.get(modal);
      openers.delete(modal);
      if (opener && document.body.contains(opener) && typeof opener.focus === 'function') opener.focus();
    }
  };

  document.addEventListener('keydown', function (event) {
    var top = stack[stack.length - 1];
    if (event.key === 'Escape' && top && top.close) { event.preventDefault(); top.close(); }
  });
})();

// Closes the theme menu after a theme option is picked (the theme itself is applied in section 1).
(function () {
  'use strict';
  var btn = document.getElementById('themeBtn');
  var menu = document.getElementById('themeMenu');
  if (!btn || !menu) return;

  menu.addEventListener('click', function (event) {
    if (!event.target.closest('[data-theme-option]')) return;
    menu.hidden = true;
    btn.setAttribute('aria-expanded', 'false');
    btn.focus(); // keyboard users land back on the toggle
  });
})();