/* Button loading state, site-wide.
   1) Every <form> that submits normally (a page navigation): the clicked submit button is disabled
      and shows a spinner, and a second submit is blocked. Forms whose own script handles the submit
      (it calls preventDefault, like the contact form) are left alone and manage their own button.
      Opt out of the automatic behaviour with data-no-loading on the form.
   2) Buttons that start work without a form (fetch on click): call
         ButtonLoading.start(button);  ...  ButtonLoading.stop(button);
   The label stays in the DOM (transparent) so the button keeps its width and its accessible name. */
(function () {
  'use strict';
  var FAILSAFE_MS = 15000; // a download or a 204 never navigates away, so give the button back

  function start(btn) {
    if (!btn || btn.getAttribute('data-loading') === 'true') return;
    btn.setAttribute('data-loading', 'true');
    btn.setAttribute('aria-busy', 'true');
    if (btn.tagName === 'INPUT') { btn.disabled = true; return; } // inputs cannot hold a spinner

    var cs = window.getComputedStyle(btn);
    var spinner = document.createElement('span');
    spinner.className = 'spinner';
    spinner.setAttribute('aria-hidden', 'true');
    spinner.setAttribute('data-btn-spinner', '');
    spinner.style.position = 'absolute';
    spinner.style.inset = '0';
    spinner.style.margin = 'auto';
    spinner.style.color = cs.color; // the spinner keeps the button's text color

    if (cs.position === 'static') { btn.style.position = 'relative'; btn.setAttribute('data-loading-pos', '1'); }
    btn.style.color = 'transparent'; // hides the label and icon but keeps the button the same size
    btn.appendChild(spinner);
    btn.disabled = true;
  }

  function stop(btn) {
    if (!btn || btn.getAttribute('data-loading') !== 'true') return;
    var spinner = btn.querySelector('[data-btn-spinner]');
    if (spinner) spinner.remove();
    btn.style.color = '';
    if (btn.getAttribute('data-loading-pos')) { btn.style.position = ''; btn.removeAttribute('data-loading-pos'); }
    btn.removeAttribute('data-loading');
    btn.setAttribute('aria-busy', 'false');
    btn.disabled = false;
  }

  window.ButtonLoading = { start: start, stop: stop };

  // Bubble phase on the document, so the form's own handlers run first and can cancel the submit
  document.addEventListener('submit', function (event) {
    var form = event.target;
    if (!form || form.tagName !== 'FORM') return;
    if (event.defaultPrevented) return; // validation failed or a script owns the request
    if (form.hasAttribute('data-no-loading') || form.getAttribute('method') === 'dialog') return;

    if (form.getAttribute('data-submitting') === 'true') { event.preventDefault(); return; } // double submit
    form.setAttribute('data-submitting', 'true');

    var btn = event.submitter || form.querySelector('button[type="submit"], button:not([type])');
    // Deferred: the browser must read the form data (including the clicked button's value) before it is disabled
    window.setTimeout(function () { start(btn); }, 0);

    window.setTimeout(function () { form.removeAttribute('data-submitting'); stop(btn); }, FAILSAFE_MS);
  });

  // Back and forward cache: coming back to the page must not show a stuck spinner
  window.addEventListener('pageshow', function (event) {
    if (!event.persisted) return;
    Array.prototype.forEach.call(document.querySelectorAll('form[data-submitting]'), function (f) { f.removeAttribute('data-submitting'); });
    Array.prototype.forEach.call(document.querySelectorAll('[data-loading="true"]'), stop);
  });
})();