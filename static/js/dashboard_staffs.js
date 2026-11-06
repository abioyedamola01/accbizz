/* Staffs page (dashboard). Loaded by templates/dashboard/staffs.html, after dashboard.js.
   Modals follow the Contents pattern: window.dashModal.opened/closed from dashboard.js.
   Uses from dashboard.js: showToast, submitForm, ajaxPost, clearFieldErrors. */
(function () {
  'use strict';

  var setShown = window.dashModal.setShown;


  function $(id) { return document.getElementById(id); }

  var body = $('staffBody');
  if (!body) return;
  var openBtn = null; // the Options button whose menu is open

  function openerFor(item) {
    return openBtn || (item.closest('.staff-menu-wrap') && item.closest('.staff-menu-wrap').querySelector('.staff-actions-btn')) || null;
  }

  // ---- Inline field errors for the add form (icon + text, role="alert", linked with aria-describedby) ----
  function clearAddErrors(form) {
    window.clearFieldErrors(form);
    form.querySelectorAll('[aria-describedby^="staffErr-"]').forEach(function (el) { el.removeAttribute('aria-describedby'); });
  }

  function showAddFieldErrors(form, errors) {
    var tpl = $('staffFieldErrorTpl');
    var firstTarget = null;
    Object.keys(errors).forEach(function (name) {
      var target = form.querySelector('[name="' + name + '"]');
      if (!target || !tpl) return; // non-field errors: the toast covers those
      var list = Array.isArray(errors[name]) ? errors[name] : [errors[name]];
      var first = list[0];
      var text = typeof first === 'string' ? first : (first && first.message) || 'Invalid value.';

      var node = tpl.content.firstElementChild.cloneNode(true);
      node.id = 'staffErr-' + name;
      node.querySelector('[data-field-error-text]').textContent = text;
      target.insertAdjacentElement('afterend', node);
      target.setAttribute('data-has-error', ''); // lets clearFieldErrors reset aria-invalid
      target.setAttribute('aria-invalid', 'true');
      target.setAttribute('aria-describedby', node.id);
      if (!firstTarget) firstTarget = target;
    });
    if (firstTarget) firstTarget.focus(); // focus the first error on submit
  }

  // ---- Reset password modal ----
  var resetModal = $('resetModal'), resetForm = $('resetForm'), resetSubmit = $('resetSubmit');
  var resetOpener = null;

  function openResetModal(item) {
    resetOpener = openerFor(item);
    resetForm.action = item.dataset.resetUrl;
    $('resetModalName').textContent = item.dataset.staffName;
    $('resetModalEmail').textContent = item.dataset.staffEmail;
    window.clearFieldErrors(resetForm);
    window.dashModal.open(resetModal, { opener: resetOpener, focus: $('resetModalCancel'), onRequestClose: closeResetModal });
  }
  function closeResetModal() {
    if (resetSubmit.disabled) return; // a request is in flight; wait for it
    window.dashModal.close(resetModal);
  }
  ['resetModalClose', 'resetModalCancel', 'resetModalOverlay'].forEach(function (id) {
    $(id).addEventListener('click', closeResetModal);
  });
  resetForm.addEventListener('submit', function (event) {
    event.preventDefault();
    window.submitForm(resetForm, {
      button: resetSubmit, spinner: $('resetSpinner'), label: $('resetSubmitLabel'),
      busyText: 'Sending...', idleText: 'Reset password',
      successFallback: 'A password reset link has been sent to the staff email.',
      onSuccess: closeResetModal
    });
  });

  // ---- Change email modal ----
  var changeModal = $('changeEmailModal'), changeForm = $('changeEmailForm'), changeSubmit = $('changeEmailSubmit');
  var changeOpener = null;

  function openChangeModal(item) {
    changeOpener = openerFor(item);
    $('changeEmailName').textContent = item.dataset.staffName;
    $('changeEmailOld').textContent = item.dataset.staffEmail;
    changeForm.elements['current_email'].value = item.dataset.staffEmail; // hidden field, sent with the post
    changeForm.elements['new_email'].value = '';
    window.clearFieldErrors(changeForm);
    window.dashModal.open(changeModal, { opener: changeOpener, focus: changeForm.elements['new_email'], onRequestClose: closeChangeModal });
  }
  function closeChangeModal() {
    if (changeSubmit.disabled) return;
    window.dashModal.close(changeModal);
  }
  ['changeEmailClose', 'changeEmailCancel', 'changeEmailOverlay'].forEach(function (id) {
    $(id).addEventListener('click', closeChangeModal);
  });
  changeForm.addEventListener('submit', function (event) {
    event.preventDefault();
    window.submitForm(changeForm, {
      button: changeSubmit, spinner: $('changeEmailSpinner'), label: $('changeEmailLabel'),
      busyText: 'Initiating...', idleText: 'Initiate change',
      successFallback: 'Email change started. A confirmation link has been sent to the new email.',
      // current_email is hidden, so show its errors under the visible field
      fieldTarget: function (name, form) { return form.elements[name === 'current_email' ? 'new_email' : name]; },
      onSuccess: closeChangeModal
    });
  });

  // ---- Options menu ----
  function menuOf(btn) { return btn.nextElementSibling; }

  function closeMenu(returnFocus) {
    if (!openBtn) return;
    var btn = openBtn;
    openBtn = null;
    menuOf(btn).hidden = true;
    btn.setAttribute('aria-expanded', 'false');
    if (returnFocus) btn.focus();
  }

  // position: fixed, so the table's scroll area cannot clip it. Lines up with the button's right
  // edge and flips above the button when there is no room below.
  function placeMenu(btn, menu) {
    var rect = btn.getBoundingClientRect();
    var width = menu.offsetWidth, height = menu.offsetHeight, gap = 8;
    var left = Math.max(8, Math.min(rect.right - width, window.innerWidth - width - 8));
    var top = rect.bottom + gap;
    if (top + height > window.innerHeight - 8 && rect.top - gap - height >= 8) top = rect.top - gap - height;
    menu.style.position = 'fixed';
    menu.style.right = 'auto';
    menu.style.bottom = 'auto';
    menu.style.left = left + 'px';
    menu.style.top = top + 'px';
  }

  function openMenuFor(btn, viaKeyboard) {
    closeMenu(false);
    var menu = menuOf(btn);
    menu.hidden = false;
    placeMenu(btn, menu);
    btn.setAttribute('aria-expanded', 'true');
    openBtn = btn;
    if (viaKeyboard) menu.querySelector('[role="menuitem"]').focus();
  }

  // ---- Remove / reinstate confirm modal ----
  var confirmModal = $('confirmModal'), confirmForm = $('confirmForm'), confirmSubmit = $('confirmSubmit');
  var confirmLabel = $('confirmSubmitLabel');
  var confirmOpener = null, confirmIdleText = 'Remove';

  var CONFIRM_ACTIONS = {
    remove: {
      title: 'Remove staff?', prefix: 'Are you sure you want to remove ', suffix: ' as staff? They will no longer be a staff member.',
      idle: 'Remove', busy: 'Removing...', fallback: 'Staff removed.', danger: true
    },
    reinstate: {
      title: 'Reinstate staff?', prefix: 'Are you sure you want to reinstate ', suffix: ' as staff? They will become a staff member again.',
      idle: 'Reinstate', busy: 'Reinstating...', fallback: 'Staff reinstated.', danger: false
    }
  };
  var confirmConfig = CONFIRM_ACTIONS.remove;

  function openConfirmModal(item) {
    var key = CONFIRM_ACTIONS[item.dataset.action] ? item.dataset.action : 'remove';
    confirmConfig = CONFIRM_ACTIONS[key];
    confirmOpener = openerFor(item);

    confirmForm.action = item.dataset.actionUrl;
    $('confirmModalTitle').textContent = confirmConfig.title;
    $('confirmModalPrefix').textContent = confirmConfig.prefix;
    $('confirmModalName').textContent = item.dataset.staffName;
    $('confirmModalSuffix').textContent = confirmConfig.suffix;
    confirmLabel.textContent = confirmConfig.idle;
    confirmIdleText = confirmConfig.idle;
    confirmModal.querySelectorAll('[data-confirm-icon]').forEach(function (chip) { chip.hidden = chip.dataset.confirmIcon !== key; });
    confirmSubmit.classList.toggle('btn-danger', confirmConfig.danger);
    confirmSubmit.classList.toggle('btn-primary', !confirmConfig.danger);

    window.dashModal.open(confirmModal, { opener: confirmOpener, focus: $('confirmModalCancel'), onRequestClose: closeConfirmModal });
  }
  function closeConfirmModal() {
    if (confirmSubmit.disabled) return;
    window.dashModal.close(confirmModal);
  }
  ['confirmModalClose', 'confirmModalCancel', 'confirmModalOverlay'].forEach(function (id) {
    $(id).addEventListener('click', closeConfirmModal);
  });
  confirmForm.addEventListener('submit', function (event) {
    event.preventDefault();
    window.submitForm(confirmForm, {
      button: confirmSubmit, spinner: $('confirmSpinner'), label: confirmLabel,
      busyText: confirmConfig.busy, idleText: confirmIdleText, successFallback: confirmConfig.fallback
      // no onSuccess: the default queues the toast and reloads the page so the row shows its new state
    });
  });

  // ---- Add staff modal ----
  var addModal = $('addStaffModal'), addForm = $('addStaffForm'), addSave = $('addStaffSaveBtn');
  var addSpinner = $('addStaffSpinner'), addLabel = $('addStaffSaveLabel'), addHint = $('addStaffHint');
  var addFormView = $('addStaffFormView'), addFooter = $('addStaffFooter');
  var addSent = $('addStaffSent'), addSentFooter = $('addStaffSentFooter');
  var addSending = false, addOpener = null;

  // Create stays off until every field is filled; the hint beside it says why
  function updateAddSaveState() {
    var filled = true;
    addForm.querySelectorAll('.add-form-required-field').forEach(function (field) {
      if (!field.value || !field.value.trim()) filled = false;
    });
    addSave.disabled = addSending || !filled;
    addHint.hidden = filled || addSending;
  }

  function showAddForm() {
    addForm.reset();
    clearAddErrors(addForm);
    addSpinner.classList.add('hidden');
    addLabel.textContent = 'Create staff';
    setShown(addSent, false);
    setShown(addSentFooter, false);
    setShown(addFormView, true, '');
    setShown(addFooter, true);
    updateAddSaveState();
  }

  function showAddSent(email) {
    $('addStaffSentEmail').textContent = email; // textContent, never innerHTML
    setShown(addFormView, false, '');
    setShown(addFooter, false);
    setShown(addSent, true);
    setShown(addSentFooter, true);
    addSent.focus();
  }

  function focusFirstAddField() {
    var first = addForm.querySelector('input, select');
    if (first) first.focus();
  }

  function openAddModal(opener) {
    addOpener = opener || $('addStaffBtn');
    showAddForm();
    window.dashModal.open(addModal, { opener: addOpener, focus: addForm.querySelector('input, select'), onRequestClose: closeAddModal });
  }
  function closeAddModal() {
    if (addSending) return;
    window.dashModal.close(addModal);
    showAddForm(); // start clean next time
  }

  $('addStaffBtn').addEventListener('click', function () { openAddModal($('addStaffBtn')); });
  ['addStaffClose', 'addStaffCancel', 'addStaffDone'].forEach(function (id) { $(id).addEventListener('click', closeAddModal); });
  $('addStaffAnother').addEventListener('click', function () { showAddForm(); focusFirstAddField(); });
  addModal.addEventListener('click', function (event) { if (event.target === addModal) closeAddModal(); }); // backdrop

  addForm.addEventListener('input', updateAddSaveState);
  addForm.addEventListener('change', updateAddSaveState);

  // success -> toast, and the modal swaps to the "link sent" message (the page does not reload)
  // failure -> inline errors from form_errors (or errors) plus an error toast
  addForm.addEventListener('submit', function (event) {
    event.preventDefault();
    if (addSending) return;
    addSending = true;

    clearAddErrors(addForm);
    addSave.disabled = true;
    addHint.hidden = true;
    addSpinner.classList.remove('hidden');
    addLabel.textContent = 'Creating...';

    var emailField = addForm.elements['email'] || addForm.elements['email_address'];
    var email = emailField ? emailField.value.trim() : '';

    window.ajaxPost(addForm).then(function (result) {
      addSending = false;
      addSpinner.classList.add('hidden');
      addLabel.textContent = 'Create staff';
      updateAddSaveState();

      if (result.ok) {
        window.showToast(result.message || 'Account creation link sent.', 'success');
        showAddSent(email);
        return;
      }
      if (result.fieldErrors) showAddFieldErrors(addForm, result.fieldErrors);
      window.showToast(result.message, 'error');
    });
  });

  // ---- Rows: one listener, so rows added later work too ----
  body.addEventListener('click', function (event) {
    var add = event.target.closest('[data-open-add-staff]');
    if (add) { openAddModal(add); return; }

    var resetBtn = event.target.closest('.staff-reset-btn');
    if (resetBtn) { closeMenu(false); openResetModal(resetBtn); return; }

    var changeBtn = event.target.closest('.staff-change-email-btn');
    if (changeBtn) { closeMenu(false); openChangeModal(changeBtn); return; }

    var activityBtn = event.target.closest('.staff-activity-btn');
    if (activityBtn) {
      var activityOpener = openBtn; // read before the menu closes
      closeMenu(false);
      window.openStaffActivity(activityBtn, activityOpener);
      return;
    }

    var confirmBtn = event.target.closest('.staff-confirm-btn');
    if (confirmBtn) { closeMenu(false); openConfirmModal(confirmBtn); return; }

    var btn = event.target.closest('.staff-actions-btn');
    if (!btn) return;
    event.preventDefault();
    if (openBtn === btn) { closeMenu(false); return; }
    openMenuFor(btn, event.detail === 0); // detail 0 = opened with the keyboard
  });

  body.addEventListener('keydown', function (event) {
    var btn = event.target.closest('.staff-actions-btn');
    if (btn && event.key === 'ArrowDown') { event.preventDefault(); openMenuFor(btn, true); return; }
    var item = event.target.closest('[role="menuitem"]');
    if (!item || !openBtn) return;
    var items = Array.prototype.slice.call(menuOf(openBtn).querySelectorAll('[role="menuitem"]'));
    var i = items.indexOf(item);
    if (event.key === 'ArrowDown') { event.preventDefault(); items[(i + 1) % items.length].focus(); }
    if (event.key === 'ArrowUp') { event.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
    if (event.key === 'Home') { event.preventDefault(); items[0].focus(); }
    if (event.key === 'End') { event.preventDefault(); items[items.length - 1].focus(); }
    if (event.key === 'Tab') closeMenu(false);
  });

  // Esc closes the menu when no modal is open (open modals handle Esc through dashModal)
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && !window.dashModal.stack.length) closeMenu(true);
  });

  // Click anywhere else closes the menu
  document.addEventListener('click', function (event) {
    if (!openBtn) return;
    if (event.target.closest('.staff-actions-btn') || event.target.closest('.staff-actions-menu')) return;
    closeMenu(false);
  });

  // A fixed menu would drift from its button, so close it on scroll or resize
  document.addEventListener('scroll', function () { closeMenu(false); }, true);
  window.addEventListener('resize', function () { closeMenu(false); });
})();