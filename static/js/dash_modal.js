/* Shared modal helper for dashboard pages: window.dashModal.
   Open/close with focus trap, Esc, focus return and body scroll lock. Load before the page script.
   Used by dashboard_staffs.js, staff_activity.js and dashboard_reports.js.
   (Belongs in dashboard.js when the dashboard base is revisited.) */
(function () {
  'use strict';
  if (window.dashModal) return;

  var FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]):not([type="hidden"]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';
  var stack = []; // open modals, last one is on top

  function visible(node) { return node.getClientRects().length > 0 && !node.closest('[hidden]'); }

  // Shows or hides an element that uses "hidden" plus a display class (default flex)
  function setShown(el, on, display) {
    el.classList.toggle('hidden', !on);
    if (display !== '') el.classList.toggle(display || 'flex', on);
  }

  window.dashModal = {
    // opts: opener (element to return focus to), focus (element to focus first), onRequestClose (called on Esc)
    open: function (el, opts) {
      opts = opts || {};
      setShown(el, true);
      document.body.classList.add('overflow-hidden');
      stack.push({ el: el, opener: opts.opener || null, onRequestClose: opts.onRequestClose });
      if (opts.focus) opts.focus.focus();
    },
    close: function (el) {
      var i = stack.map(function (s) { return s.el; }).indexOf(el);
      var entry = i > -1 ? stack.splice(i, 1)[0] : null;
      setShown(el, false);
      if (!stack.length) document.body.classList.remove('overflow-hidden');
      if (entry && entry.opener && document.contains(entry.opener)) entry.opener.focus();
    }
  };

  document.addEventListener('keydown', function (event) {
    var top = stack[stack.length - 1];
    if (!top) return;
    if (event.key === 'Escape') {
      if (top.onRequestClose) { event.preventDefault(); top.onRequestClose(); }
      return;
    }
    if (event.key !== 'Tab') return;
    var items = Array.prototype.slice.call(top.el.querySelectorAll(FOCUSABLE)).filter(visible);
    if (!items.length) return;
    var first = items[0], last = items[items.length - 1];
    if (event.shiftKey && (document.activeElement === first || !top.el.contains(document.activeElement))) {
      event.preventDefault(); last.focus();
    } else if (!event.shiftKey && (document.activeElement === last || !top.el.contains(document.activeElement))) {
      event.preventDefault(); first.focus();
    }
  });

  window.dashModal.setShown = setShown;
  window.dashModal.stack = stack;
})();