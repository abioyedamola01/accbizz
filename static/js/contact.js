/* Contact form: validation (on blur, then on change), focus the first error on submit,
   AJAX submit to the existing endpoint, success state. Loaded only by main/contact.html.
   Server contract (unchanged): JSON { ok, errors: { field: [msg] , __all__: [msg] }, message }. */
(function () {
  'use strict';
  var form = document.getElementById('contactForm');
  if (!form) return;

  var submitBtn = document.getElementById('contactSubmit');
  var spinner = document.getElementById('contactSpinner');
  var submitLabel = document.getElementById('contactSubmitLabel');
  var banner = document.getElementById('contactError');
  var successEl = document.getElementById('contactSuccess');
  var successEmail = document.getElementById('contactSuccessEmail');
  var another = document.getElementById('contactAnother');
  var busy = false;
  var lostFocus = false; // true when the submit button had focus as it was disabled

  var nameInput = form.querySelector('[name="name"]');
  var emailInput = form.querySelector('[name="email"]');
  var messageInput = form.querySelector('[name="message"]');
  var serviceSelect = form.querySelector('[name="service"]');

  // Client checks. The server checks again, so these only save a round trip.
  var rules = [
    { el: nameInput, check: function (v) { return v.trim() ? '' : 'Enter your name.'; } },
    { el: emailInput, check: function (v) {
        if (!v.trim()) return 'Enter your email address so we can reply.';
        return emailInput.checkValidity() ? '' : 'Enter a valid email address, like you@example.com.';
    } },
    { el: messageInput, check: function (v) { return v.trim() ? '' : 'Write a short message about what you need.'; } }
  ].filter(function (r) { return r.el; });

  function parts(control) {
    return {
      help: document.getElementById(control.id + '-help'),
      err: document.getElementById(control.id + '-error')
    };
  }

  function setError(control, message) {
    var p = parts(control);
    if (!p.err) return;
    p.err.querySelector('[data-msg]').textContent = message; // textContent, never innerHTML
    p.err.hidden = false;
    p.err.classList.remove('field-msg-in');
    void p.err.offsetWidth; // restart the fade-in
    p.err.classList.add('field-msg-in');
    if (p.help) p.help.hidden = true; // the error replaces the helper text
    control.setAttribute('aria-invalid', 'true');
    control.setAttribute('aria-describedby', p.err.id);
  }

  function clearError(control) {
    var p = parts(control);
    if (p.err) { p.err.hidden = true; p.err.classList.remove('field-msg-in'); p.err.querySelector('[data-msg]').textContent = ''; }
    if (p.help) p.help.hidden = false;
    control.removeAttribute('aria-invalid');
    if (p.help) control.setAttribute('aria-describedby', p.help.id); else control.removeAttribute('aria-describedby');
  }

  function showBanner(message) {
    banner.querySelector('[data-msg]').textContent = message;
    banner.hidden = false;
  }
  function hideBanner() { banner.hidden = true; banner.querySelector('[data-msg]').textContent = ''; }

  function validate(rule) {
    var message = rule.check(rule.el.value);
    if (message) setError(rule.el, message); else clearError(rule.el);
    return !message;
  }

  // Validate on blur, then on every change once the field has been visited
  rules.forEach(function (rule) {
    var touched = false;
    rule.el.addEventListener('blur', function () { touched = true; validate(rule); });
    ['input', 'change'].forEach(function (type) {
      rule.el.addEventListener(type, function () { if (touched || rule.el.hasAttribute('aria-invalid')) validate(rule); });
    });
  });

  // Optional fields: clear a server error as soon as the person edits the field
  [form.querySelector('[name="phone"]'), serviceSelect].forEach(function (el) {
    if (!el) return;
    ['input', 'change'].forEach(function (type) {
      el.addEventListener(type, function () { if (el.hasAttribute('aria-invalid')) clearError(el); });
    });
  });

  function clearAll() {
    Array.prototype.forEach.call(form.querySelectorAll('[aria-invalid]'), clearError);
    hideBanner();
  }

  // Disabled plus a spinner while the request runs, so a second click can't send the message twice.
  // The button width does not change (the label stays about the same length and the button is full width).
  function setBusy(on) {
    var hadFocus = document.activeElement === submitBtn;
    busy = on;
    submitBtn.disabled = on;
    submitBtn.setAttribute('aria-busy', on ? 'true' : 'false');
    spinner.hidden = !on;
    submitLabel.textContent = on ? 'Sending message' : 'Send message';
    // A disabled button drops focus; give it back when the request ends and nothing else has focus
    if (!on && hadFocus === false && lostFocus && (document.activeElement === document.body || !document.activeElement)) submitBtn.focus();
    lostFocus = on && hadFocus;
  }

  function firstMessage(value) {
    var first = Array.isArray(value) ? value[0] : value;
    return typeof first === 'string' ? first : (first && first.message) || 'Check this field and try again.';
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

  // errors: { email: ["Enter a valid email address."], __all__: ["..."] }. Returns the first control that got a message.
  function showServerErrors(errors) {
    var firstControl = null;
    Object.keys(errors).forEach(function (key) {
      var message = firstMessage(errors[key]);
      var control = key === '__all__' ? null : form.querySelector('[name="' + key + '"]');
      if (control && control.type !== 'hidden') {
        setError(control, message);
        if (!firstControl) firstControl = control;
      } else if (banner.hidden) {
        showBanner(message);
      }
    });
    return firstControl;
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    if (busy) return;
    clearAll();

    // Check every required field so all errors show at once, then focus the first one on the page
    var firstBad = null;
    rules.forEach(function (rule) { if (!validate(rule) && !firstBad) firstBad = rule.el; });
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
        var serverError = data && typeof data.error === 'string' ? data.error : '';
        if (result.response.ok && data && data.ok !== false && !serverError) { showSuccess(); return; }
        if (!data) { showBanner("Couldn't send your message. The server had a problem, so try again in a moment."); return; }
        var fieldErrors = parseFieldErrors(data);
        var control = fieldErrors ? showServerErrors(fieldErrors) : null;
        if (data.message || serverError) showBanner(data.message || serverError);
        else if (!control && banner.hidden) showBanner("Couldn't send your message. Check the details and try again.");
        if (control) control.focus(); else if (!banner.hidden) banner.scrollIntoView({ block: 'nearest' });
      })
      .catch(function (error) {
        showBanner(error && error.name === 'AbortError'
          ? "Couldn't send your message because the request timed out. Check your connection and try again."
          : "Couldn't send your message. Check your connection and try again.");
      })
      .finally(function () {
        clearTimeout(timer);
        setBusy(false);
      });
  });

  function showSuccess() {
    // Umami custom event: the message was saved. Guarded so a blocked tracker can't break the form.
    try { if (window.umami) window.umami.track('contact-form-success'); } catch (e) {}
    successEmail.textContent = emailInput.value.trim();
    form.hidden = true;
    successEl.hidden = false;
    successEl.focus();
  }

  if (another) {
    another.addEventListener('click', function () {
      // Keep name, email and phone so a second message is quick; clear the rest
      messageInput.value = '';
      if (serviceSelect) serviceSelect.selectedIndex = 0; // back to General enquiry
      clearAll();
      successEl.hidden = true;
      form.hidden = false;
      messageInput.focus();
    });
  }
})();