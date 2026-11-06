/* Staff pages: login, OTP, reset password, create account, change password, change and revert email.
   Loaded by base/staffs/base.html. Plain JS, no dependencies. Content works without it (plain form posts).
   Classes added from here (hidden, flex, text-small, text-danger-fg and friends) are also written in the templates, so the Tailwind build includes them. */
(function () {
  'use strict';

  var doc = document;

  /* ---------- Shared helpers ---------- */

  function byId(id) { return doc.getElementById(id); }
  function all(sel, root) { return Array.prototype.slice.call((root || doc).querySelectorAll(sel)); }

  function announce(text) {
    var el = byId('staffs-live');
    if (!el || !text) return;
    el.textContent = '';
    setTimeout(function () { el.textContent = text; }, 30);
  }

  var storage = {
    get: function (k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { sessionStorage.setItem(k, v); } catch (e) { /* storage unavailable */ } },
    remove: function (k) { try { sessionStorage.removeItem(k); } catch (e) { /* storage unavailable */ } }
  };

  /* Button busy state: disabled, aria-busy, spinner shown, label swapped for data-busy-label.
     Pass keepDisabled when turning busy off and the button should stay disabled (the form is not ready yet). */
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
      if (isLink) { btn.setAttribute('aria-disabled', 'true'); btn.setAttribute('tabindex', '-1'); }
      else { btn.disabled = true; }
      if (spinner) spinner.classList.remove('hidden');
      if (label && busyLabel) label.textContent = busyLabel;
      if (busyLabel) announce(busyLabel);
    } else {
      btn.removeAttribute('aria-busy');
      btn.removeAttribute('data-busy');
      if (isLink) { btn.removeAttribute('aria-disabled'); btn.removeAttribute('tabindex'); }
      else { btn.disabled = !!keepDisabled; }
      if (spinner) spinner.classList.add('hidden');
      if (label && btn.getAttribute('data-idle-label') !== null) label.textContent = btn.getAttribute('data-idle-label');
    }
  }
  window.setButtonBusy = window.setButtonBusy || setBusy;

  /* Inline field error with icon. The container sits inside a [data-field] wrapper; every text input in it gets aria-invalid. */
  var ERR_ICON = '<svg class="shrink-0 mt-1" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z"/></svg>';

  function markInvalid(field, invalid) {
    all('input:not([type="hidden"])', field).forEach(function (input) {
      if (invalid) input.setAttribute('aria-invalid', 'true'); else input.removeAttribute('aria-invalid');
    });
  }

  function setFieldError(container, text) {
    if (!container) return;
    container.innerHTML = '';
    if (text) {
      var p = doc.createElement('p');
      p.className = 'flex items-start gap-2 text-small text-danger-fg';
      p.innerHTML = ERR_ICON;
      var span = doc.createElement('span');
      span.textContent = text; // textContent, never innerHTML
      p.appendChild(span);
      container.appendChild(p);
    }
    var field = container.closest('[data-field]');
    if (field) markInvalid(field, !!text);
  }

  /* ---------- Generic: busy on submit, busy on click, password toggle ---------- */

  if (!window.__staffsBusyBound) {
    window.__staffsBusyBound = true;

    // Runs after the page's own submit handlers (document, bubble phase), so a form they stopped is left alone.
    doc.addEventListener('submit', function (e) {
      var form = e.target;
      if (!form || !form.hasAttribute || !form.hasAttribute('data-busy-form')) return;
      if (e.defaultPrevented) return;
      if (form.getAttribute('data-submitting') === 'true') { e.preventDefault(); return; }
      form.setAttribute('data-submitting', 'true');
      setBusy(e.submitter || form.querySelector('[type="submit"]'), true);
    });

    doc.addEventListener('click', function (e) {
      var el = e.target.closest ? e.target.closest('[data-busy-click]') : null;
      if (!el) return;
      if (el.getAttribute('data-busy') === 'true') { e.preventDefault(); return; }
      if (el.type === 'submit') return; // submit buttons are handled on submit, so a failed check does not lock them
      setBusy(el, true);
    });

    // Back button restored the page from the cache: nothing is submitting any more.
    window.addEventListener('pageshow', function (e) {
      if (!e.persisted) return;
      all('[data-submitting]').forEach(function (f) { f.removeAttribute('data-submitting'); });
      all('[data-busy="true"]').forEach(function (b) { setBusy(b, false); });
      doc.dispatchEvent(new CustomEvent('staffs:reset'));
    });
  }

  function setPasswordHidden(btn, hidden) {
    var input = byId(btn.getAttribute('data-target'));
    if (!input) return;
    input.type = hidden ? 'password' : 'text';
    var open = btn.querySelector('[data-icon="eye-open"]');
    var closed = btn.querySelector('[data-icon="eye-closed"]');
    if (open) open.classList.toggle('hidden', !hidden);
    if (closed) closed.classList.toggle('hidden', hidden);
    btn.setAttribute('aria-pressed', hidden ? 'false' : 'true');
    btn.setAttribute('aria-label', hidden ? 'Show password' : 'Hide password');
  }

  doc.addEventListener('click', function (e) {
    var btn = e.target.closest ? e.target.closest('.toggle-password') : null;
    if (!btn) return;
    var input = byId(btn.getAttribute('data-target'));
    if (input) setPasswordHidden(btn, input.type !== 'password');
  });

  /* Server errors on load: mark the fields and focus the first one. */
  function initServerErrors() {
    var first = null;
    all('[data-field]').forEach(function (field) {
      if (field.querySelector('[data-server-error]')) {
        markInvalid(field, true);
        if (!first) first = field.querySelector('input:not([type="hidden"])');
      }
    });
    if (first && !doc.querySelector('[data-status-root][data-status]:not([data-status=""])')) first.focus();
  }

  /* ---------- Login ---------- */

  function initLogin() {
    var form = byId('loginForm');
    var terms = byId('acceptPolicy');
    if (!form || !terms) return;
    var termsErrors = byId('termsErrors');

    terms.addEventListener('change', function () { if (terms.checked) setFieldError(termsErrors, ''); });
    form.addEventListener('submit', function (e) {
      if (terms.checked) return;
      e.preventDefault();
      setFieldError(termsErrors, 'Accept the terms and conditions to log in.');
      terms.focus();
    });
  }

  /* ---------- OTP ---------- */

  function initOtp() {
    var form = byId('otpForm');
    if (!form) return;

    var inputs = all('.otp-input', form);
    var codeField = byId('otpCode');
    var verifyButton = byId('verifyButton');
    var otpErrors = byId('otpErrors');

    function isComplete() {
      return inputs.every(function (input) { return /^[0-9]$/.test(input.value); });
    }

    function checkComplete() {
      codeField.value = inputs.map(function (input) { return input.value; }).join('');
      if (form.getAttribute('data-submitting') === 'true') return;
      verifyButton.disabled = !isComplete();
      if (isComplete()) setFieldError(otpErrors, '');
    }

    inputs.forEach(function (input, index) {
      input.addEventListener('input', function () {
        input.value = input.value.replace(/[^0-9]/g, '').slice(0, 1);
        if (input.value && index < inputs.length - 1) inputs[index + 1].focus();
        checkComplete();
      });
      input.addEventListener('keydown', function (e) {
        if (e.key === 'Backspace' && !input.value && index > 0) inputs[index - 1].focus();
      });
      input.addEventListener('focus', function () { input.select(); });
      input.addEventListener('paste', function (e) {
        e.preventDefault();
        var pasted = ((e.clipboardData || window.clipboardData).getData('text') || '').replace(/[^0-9]/g, '');
        if (!pasted) return;
        inputs.forEach(function (el, i) { el.value = pasted[i] || ''; });
        var next = inputs.findIndex(function (el) { return !el.value; });
        inputs[next === -1 ? inputs.length - 1 : next].focus();
        checkComplete();
      });
    });

    form.addEventListener('submit', function (e) {
      if (!isComplete()) {
        e.preventDefault();
        setFieldError(otpErrors, 'Enter all 6 digits of the code.');
        var empty = inputs.filter(function (el) { return !el.value; })[0];
        (empty || inputs[0]).focus();
        return;
      }
      codeField.value = inputs.map(function (input) { return input.value; }).join('');
    });

    doc.addEventListener('staffs:reset', checkComplete);
    checkComplete();

    // Resend countdown. A new countdown starts only when the page carries a new code (different otp uuid);
    // reloading after a wrong code resumes the time that is left.
    var timerEl = byId('resendTimer');
    var waitEl = doc.querySelector('[data-resend-wait]');
    var readyEl = doc.querySelector('[data-resend-ready]');
    var resendLink = byId('resendLink');
    if (!timerEl || !waitEl || !readyEl) return;

    var SECONDS = 60;
    var EXPIRY_KEY = 'otpResendExpiresAt';
    var UUID_KEY = 'otpResendUuid';
    var uuid = form.getAttribute('data-otp-uuid') || '';
    var intervalId = null;

    function format(total) {
      return String(Math.floor(total / 60)).padStart(2, '0') + ':' + String(total % 60).padStart(2, '0');
    }

    function render() {
      var stored = storage.get(EXPIRY_KEY);
      var expiry = stored ? parseInt(stored, 10) : null;
      var now = Date.now();
      if (!expiry || expiry <= now) {
        if (intervalId) clearInterval(intervalId);
        waitEl.classList.add('hidden');
        readyEl.classList.remove('hidden');
        return;
      }
      waitEl.classList.remove('hidden');
      readyEl.classList.add('hidden');
      timerEl.textContent = format(Math.ceil((expiry - now) / 1000));
    }

    if (!uuid || storage.get(UUID_KEY) !== uuid) {
      storage.set(EXPIRY_KEY, String(Date.now() + SECONDS * 1000));
      storage.set(UUID_KEY, uuid);
    }
    render();
    intervalId = setInterval(render, 1000);

    // The link is a normal navigation to the resend view. Wipe the old countdown first so the fresh page starts a new one.
    if (resendLink) resendLink.addEventListener('click', function () {
      storage.remove(EXPIRY_KEY);
      storage.remove(UUID_KEY);
    });
  }

  /* ---------- Forms that post with fetch and show a status panel (reset password, create account, change email, revert email) ---------- */

  function initAjaxForm(form) {
    var root = form.closest('[data-status-root]') || doc;
    var fields = all('[data-field]', form);
    var primary = fields[0] ? fields[0].querySelector('input:not([type="hidden"])') : null;
    var confirm = fields[1] ? fields[1].querySelector('input:not([type="hidden"])') : null;
    var primaryErrors = fields[0] ? fields[0].querySelector('[data-field-errors]') : null;
    var confirmErrors = fields[1] ? fields[1].querySelector('[data-field-errors]') : null;
    var button = form.querySelector('[type="submit"]');
    var cfg = form.dataset;
    var TIMEOUT_MS = 15000;
    var busy = false;

    if (!primary || !button) return;

    function showStatus(key) {
      var panel = root.querySelector('[data-status-panel="' + key + '"]') || root.querySelector('[data-status-panel="unknown"]');
      if (!panel) return;
      var wrap = root.querySelector('[data-status-form-wrap]');
      var title = root.querySelector('[data-status-title]');
      var intro = root.querySelector('[data-status-intro]');
      if (wrap) wrap.classList.add('hidden');
      if (intro) intro.classList.add('hidden');
      if (title && panel.getAttribute('data-title')) title.textContent = panel.getAttribute('data-title');
      panel.classList.remove('hidden');
      panel.focus();
    }

    function checkMatch() {
      if (confirm && confirm.value && primary.value !== confirm.value) {
        setFieldError(confirmErrors, 'Passwords do not match.');
        return false;
      }
      setFieldError(confirmErrors, '');
      return true;
    }

    primary.addEventListener('input', function () {
      setFieldError(primaryErrors, '');
      if (confirm && confirm.value) checkMatch();
    });
    if (confirm) {
      confirm.addEventListener('input', checkMatch);
      confirm.addEventListener('blur', checkMatch);
    }

    // The view renders the page again when saving fails or the link has a status. Read both out of that HTML.
    function parseHtml(html) {
      var parsed = new DOMParser().parseFromString(html, 'text/html');
      var marker = parsed.querySelector('[data-status-root]');
      var errors = [];
      all('[data-server-error]', parsed).forEach(function (el) {
        var text = el.textContent.trim();
        if (text && errors.indexOf(text) === -1) errors.push(text);
      });
      return { status: marker ? (marker.getAttribute('data-status') || '') : '', errors: errors };
    }

    // Field errors from the JSON response: `form_errors` (new) or `errors` (older views).
    // Either an object or a JSON string, for example form.errors.as_json(). Returns an object or null.
    function parseFieldErrors(data) {
      var raw = data.form_errors || data.errors;
      if (typeof raw === 'string') {
        try { raw = JSON.parse(raw); } catch (e) { return null; }
      }
      return raw && typeof raw === 'object' ? raw : null;
    }

    function firstMessage(value) {
      var first = Array.isArray(value) ? value[0] : value;
      return typeof first === 'string' ? first : (first && first.message) || 'Check this field and try again.';
    }

    // Puts each message under the matching field. Other keys (such as __all__) are left to the toast.
    function showFieldErrors(errors) {
      if (!errors) return;
      var firstControl = null;
      Object.keys(errors).forEach(function (name) {
        var text = firstMessage(errors[name]);
        if (primary.name === name) { setFieldError(primaryErrors, text); if (!firstControl) firstControl = primary; }
        else if (confirm && confirm.name === name) { setFieldError(confirmErrors, text); if (!firstControl) firstControl = confirm; }
      });
      if (firstControl) firstControl.focus();
    }

    // Always resolves to { ok, status, message, fieldErrors }
    function send() {
      var controller = new AbortController();
      var timer = setTimeout(function () { controller.abort(); }, TIMEOUT_MS);

      return fetch(form.getAttribute('action') || window.location.href, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },
        credentials: 'same-origin',
        signal: controller.signal
      })
        .then(function (response) {
          return response.text().then(function (text) {
            var data = null;
            try { data = JSON.parse(text); } catch (e) { /* not JSON: a normal page render */ }

            if (data && typeof data === 'object') {
              var serverError = typeof data.error === 'string' ? data.error : '';
              var ok = response.ok && data.ok !== false && !serverError;
              return {
                ok: ok,
                status: ok ? 'success' : '',
                message: data.message || serverError || (ok ? cfg.successMsg : 'Something went wrong. Please try again.'),
                fieldErrors: ok ? null : parseFieldErrors(data)
              };
            }
            if (response.status === 403) return { ok: false, status: '', message: 'This page has expired. Refresh it and try again.' };
            if (response.status >= 500) return { ok: false, status: '', message: 'Server error. Please try again in a moment.' };

            var parsed = parseHtml(text);
            if (parsed.status === 'success') return { ok: true, status: 'success', message: cfg.successMsg };
            if (parsed.status) return { ok: false, status: parsed.status, message: '' }; // the form can no longer be used
            return { ok: false, status: '', message: parsed.errors.length ? parsed.errors.join(' ') : cfg.failMsg };
          });
        })
        .catch(function (error) {
          var timedOut = !!error && error.name === 'AbortError';
          return { ok: false, status: '', message: timedOut ? 'The request timed out. Please try again.' : 'Network error. Check your connection and try again.' };
        })
        .finally(function () { clearTimeout(timer); });
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (busy) return;

      setFieldError(primaryErrors, '');
      setFieldError(confirmErrors, '');

      if (!primary.value) {
        setFieldError(primaryErrors, cfg.emptyMsg);
        primary.focus();
        return;
      }
      if (confirm && !confirm.value) {
        setFieldError(confirmErrors, cfg.confirmEmptyMsg);
        confirm.focus();
        return;
      }
      if (!checkMatch()) { confirm.focus(); return; }

      busy = true;
      setBusy(button, true);
      send().then(function (result) {
        busy = false;
        setBusy(button, false);
        if (result.status && result.status !== 'success') {
          showStatus(result.status); // the panel says it all, so no toast
        } else if (result.ok) {
          if (window.showToast) window.showToast(result.message, 'success');
          showStatus('success');
        } else {
          showFieldErrors(result.fieldErrors);
          if (window.showToast) window.showToast(result.message, 'error');
        }
      });
    });
  }

  /* ---------- Change password (accordion, normal post, idle lock) ---------- */

  function initChangePassword(form) {
    var IDLE_TIMEOUT_MS = 5 * 60 * 1000; // no typing or clicking for 5 minutes: clear and lock the form
    var SUBMIT_TIMEOUT_MS = 30 * 1000;   // no answer for 30 seconds: stop waiting

    var accordion = byId('pwAccordion');
    var inputs = all('[data-acc-input]', form); // old, new, confirm
    if (!accordion || inputs.length < 3) return;

    var oldPw = inputs[0], newPw = inputs[1], confirmPw = inputs[2];
    var items = all('.pw-acc-item', accordion);
    var confirmError = byId('confirmError');
    var submitButton = byId('submitButton');
    var idleNotice = byId('idleNotice');
    var idleRestart = byId('idleRestart');
    var slowNotice = byId('slowNotice');

    var submitting = false, locked = false, submitTimer = null, lastActivity = Date.now();

    function openItem(index, focusInput) {
      items.forEach(function (item, i) {
        var open = i === index;
        item.querySelector('.pw-acc-panel').classList.toggle('is-open', open);
        item.querySelector('.pw-acc-head').setAttribute('aria-expanded', open ? 'true' : 'false');
      });
      if (focusInput && !inputs[index].disabled) inputs[index].focus();
    }

    items.forEach(function (item, i) {
      item.querySelector('.pw-acc-head').addEventListener('click', function () { openItem(i, true); });
    });

    // Enter moves to the next field instead of posting half a form
    inputs.forEach(function (input, i) {
      input.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter') return;
        if (i < inputs.length - 1) { e.preventDefault(); openItem(i + 1, true); }
        else if (!isReady()) { e.preventDefault(); }
      });
    });

    var start = items.findIndex(function (item) { return item.hasAttribute('data-open'); });
    openItem(start < 0 ? 0 : start, false);
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { accordion.classList.add('pw-acc-ready'); });
    });

    function isReady() {
      return oldPw.value !== '' && newPw.value !== '' && confirmPw.value !== '' && newPw.value === confirmPw.value;
    }

    // The note on each row: a tick when filled, a word when it needs attention
    function renderStatus(i) {
      var el = items[i].querySelector('.pw-acc-status');
      var text = '', tone = '';
      if (items[i].getAttribute('data-err') === '1') { text = 'Needs attention'; tone = 'err'; }
      else if (i === 2 && confirmPw.value !== '' && confirmPw.value !== newPw.value) { text = "Doesn't match"; tone = 'err'; }
      else if (inputs[i].value !== '') { text = 'Filled'; tone = 'ok'; }
      el.textContent = text;
      el.className = 'pw-acc-status' + (tone ? ' pw-acc-status--' + tone : '');
    }

    function updateState() {
      var mismatch = confirmPw.value !== '' && confirmPw.value !== newPw.value;
      confirmError.classList.toggle('hidden', !mismatch);
      if (mismatch) confirmPw.setAttribute('aria-invalid', 'true'); else confirmPw.removeAttribute('aria-invalid');
      items.forEach(function (item, i) { renderStatus(i); });
      if (!submitting) submitButton.disabled = locked || !isReady();
    }

    inputs.forEach(function (input, i) {
      input.addEventListener('input', function () {
        items[i].setAttribute('data-err', ''); // the server's complaint no longer applies once the field is edited
        updateState();
      });
    });

    function setSubmitting(value) {
      submitting = value;
      if (value) setBusy(submitButton, true); else setBusy(submitButton, false, true);
      updateState();
    }

    form.addEventListener('submit', function (e) {
      if (submitting || locked || !isReady()) { e.preventDefault(); return; }
      slowNotice.classList.add('hidden');
      setSubmitting(true);
      if (SUBMIT_TIMEOUT_MS > 0) {
        submitTimer = setTimeout(function () {
          try { window.stop(); } catch (err) { /* cancels the request that is still waiting */ }
          setSubmitting(false);
          lastActivity = Date.now();
          slowNotice.classList.remove('hidden');
        }, SUBMIT_TIMEOUT_MS);
      }
    });

    doc.addEventListener('staffs:reset', function () { clearTimeout(submitTimer); setSubmitting(false); });

    function lockForm() {
      locked = true;
      inputs.forEach(function (input, i) {
        input.value = '';
        input.disabled = true;
        items[i].setAttribute('data-err', '');
      });
      all('.toggle-password', form).forEach(function (btn) { setPasswordHidden(btn, true); });
      openItem(0, false);
      slowNotice.classList.add('hidden');
      idleNotice.classList.remove('hidden');
      updateState();
      idleRestart.focus();
    }

    function checkIdle() {
      if (IDLE_TIMEOUT_MS > 0 && !submitting && !locked && Date.now() - lastActivity >= IDLE_TIMEOUT_MS) lockForm();
    }

    ['input', 'keydown', 'pointerdown', 'focusin'].forEach(function (name) {
      form.addEventListener(name, function () { lastActivity = Date.now(); });
    });

    // Timestamps rather than one long timer, because background tabs throttle timers
    setInterval(checkIdle, 10 * 1000);
    doc.addEventListener('visibilitychange', function () { if (!doc.hidden) checkIdle(); });

    // A fresh page load gives a fresh form (and sends you to the login page if your session ended)
    idleRestart.addEventListener('click', function () { window.location.reload(); });

    updateState();
  }

  /* ---------- Start ---------- */

  function start() {
    initServerErrors();
    initLogin();
    initOtp();
    all('form[data-ajax-form]').forEach(initAjaxForm);
    var change = byId('changePasswordForm');
    if (change) initChangePassword(change);
  }

  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', start); else start();
})();