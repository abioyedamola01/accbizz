/* Dashboard > Communication. Loaded by templates/dashboard/communication.html.
   Needs window.showToast and window.ajaxPost from dashboard.js (loaded earlier in the base).
   No Tailwind classes are set here: row and status styling follows data-attended on the row
   and data-state on the status elements, which the templates style. */
(function () {
  'use strict';

  var app = document.getElementById('msgApp');
  if (!app) return;

  // WhatsApp links need the number with its country code. Numbers that start
  // with 0 are treated as local and get this code in front of them.
  var DEFAULT_COUNTRY_CODE = app.dataset.countryCode || '234';
  // Django needs a number to build the URL, so a placeholder is swapped for the real batch point.
  var BATCH_URL_TEMPLATE = app.dataset.batchUrl;

  function $(id) { return document.getElementById(id); }

  var body = $('msgBody');
  var actionForm = $('msgActionForm');
  var modal = $('msgModal');
  var deleteModal = $('msgDeleteModal');
  var current = null;        // the row open in the detail dialog
  var opener = null;         // the row button to give focus back to
  var activeFilter = 'all';
  var deleting = false;
  var announceTimer = null;

  // Plain display toggle. An inline style beats the .btn display rule.
  function setVisible(el, visible) { el.style.display = visible ? '' : 'none'; }

  function openDialog(dlg) {
    if (typeof dlg.showModal === 'function') dlg.showModal();
    else dlg.setAttribute('open', '');
  }
  function closeDialog(dlg) {
    if (typeof dlg.close === 'function') dlg.close();
    else dlg.removeAttribute('open');
  }

  // Click on the dialog element itself means the backdrop was clicked
  [modal, deleteModal].forEach(function (dlg) {
    dlg.addEventListener('click', function (event) {
      if (event.target === dlg && !(dlg === deleteModal && deleting)) closeDialog(dlg);
    });
  });

  // ---- Reading a row ----
  function isAttended(row) { return row.dataset.attended === '1'; }
  function isMine(row) { return row.dataset.mine === '1'; }
  function attendedBy(row) { return isMine(row) ? 'you' : (row.dataset.attendedBy || 'someone'); }

  // ---- Painting a row. Dot and name weight react to data-attended in CSS. ----
  function paintRow(row) {
    var attended = isAttended(row);
    var status = row.querySelector('.msg-status');
    status.dataset.state = attended ? 'attended' : 'unattended';
    status.textContent = attended ? 'Attended by ' + attendedBy(row) : 'Unattended';
  }

  function applyState(row, state) {
    var wasAttended = isAttended(row);
    row.dataset.attended = state.is_attended ? '1' : '0';
    row.dataset.attendedBy = state.attended_by || '';
    row.dataset.mine = state.attended_by_is_you ? '1' : '0';
    row.dataset.attendedAgo = state.attended_ago || '';
    paintRow(row);

    // Only a real change moves the count, so repeating a state never double counts
    if (wasAttended !== state.is_attended) {
      counts.unattended += state.is_attended ? -1 : 1;
      renderCounts();
    }
    if (current === row) fillModalStatus();
    applyFilter(false);
  }

  // Counts arrive once with the page, then the page keeps the maths itself:
  // attend -1 unattended, unattend +1, delete -1 total (and -1 unattended if it was unattended).
  var counts = {
    total: parseInt($('msgTotalBadge').dataset.count, 10) || 0,
    unattended: parseInt($('msgUnattendedBadge').dataset.count, 10) || 0
  };

  function renderCounts() {
    counts.total = Math.max(0, counts.total);
    counts.unattended = Math.max(0, counts.unattended);
    $('msgTotalBadge').textContent = counts.total + (counts.total === 1 ? ' message' : ' messages');
    $('msgUnattendedBadge').textContent = counts.unattended + ' unattended';
    var sidebar = document.querySelector('[data-unattended-badge]');
    if (sidebar) {
      sidebar.textContent = counts.unattended > 99 ? '99+' : counts.unattended;
      setVisible(sidebar, counts.unattended !== 0);
    }
  }

  // ---- Filter tabs and search (they work on the rows loaded so far) ----
  function applyFilter(announce) {
    var q = $('msgSearch').value.trim().toLowerCase();
    var rows = body.querySelectorAll('tr.msg-row');
    var visible = 0;

    rows.forEach(function (row) {
      var attended = isAttended(row);
      var matchesTab = activeFilter === 'all' ||
        (activeFilter === 'attended' && attended) ||
        (activeFilter === 'unattended' && !attended);
      var haystack = (row.dataset.name + ' ' + row.dataset.email + ' ' + row.dataset.phone + ' ' +
        row.dataset.service + ' ' + row.dataset.message).toLowerCase();
      var show = matchesTab && (!q || haystack.indexOf(q) !== -1);
      row.hidden = !show;
      if (show) visible++;
    });

    $('msgEmpty').hidden = rows.length > 0;
    $('msgFilterEmpty').hidden = rows.length === 0 || visible > 0;

    if (announce) {
      clearTimeout(announceTimer);
      announceTimer = setTimeout(function () {
        $('msgResult').textContent = 'Showing ' + visible + ' of ' + rows.length + ' loaded message' + (rows.length === 1 ? '' : 's') + '.';
      }, 400);
    }
  }

  function setTab(filter) {
    activeFilter = filter;
    document.querySelectorAll('.msg-tab').forEach(function (t) {
      t.setAttribute('aria-pressed', t.dataset.filter === filter ? 'true' : 'false');
    });
  }

  $('msgTabs').addEventListener('click', function (event) {
    var tab = event.target.closest('.msg-tab');
    if (!tab) return;
    setTab(tab.dataset.filter);
    applyFilter(true);
  });
  $('msgSearch').addEventListener('input', function () { applyFilter(true); });
  $('msgClear').addEventListener('click', function () {
    setTab('all');
    $('msgSearch').value = '';
    applyFilter(true);
    $('msgSearch').focus();
  });

  // ---- Server actions ----
  function post(url) {
    actionForm.action = url;
    return window.ajaxPost(actionForm);
  }

  // One request at a time per message. A second click, or a reply click that
  // races the button, is ignored while the first is still running.
  function guarded(row, task) {
    if (row.dataset.busy === '1') return Promise.resolve({ ok: false, skipped: true });
    row.dataset.busy = '1';
    return task().finally(function () { delete row.dataset.busy; });
  }

  // If the server says "ok" but sends no "state", work the row's state out here.
  // A real "state" from the server always wins. Counts are never guessed.
  function withFallback(r, nowAttended) {
    var d = r.data || (r.data = {});
    if (!r.ok) return d;
    if (!d.state) {
      d.state = nowAttended
        ? { is_attended: true, attended_by: '', attended_by_is_you: true, attended_ago: 'just now' }
        : { is_attended: false, attended_by: '', attended_by_is_you: false, attended_ago: '' };
    }
    return d;
  }

  // quiet = true when triggered by a reply click: no success toast
  function attend(row, quiet) {
    return guarded(row, function () {
      return post(row.dataset.attendUrl).then(function (r) {
        if (r.skipped) return r;
        var d = withFallback(r, true);
        if (d.state) applyState(row, d.state);
        if (!r.ok) {
          window.showToast(r.message || "Couldn't update the message. Try again.", 'error');
        } else if (!quiet) {
          window.showToast(r.message || 'Marked as attended.', 'success');
        } else if (d.state && !d.state.attended_by_is_you) {
          // Someone got there first: tell them, but do not block the reply
          window.showToast(r.message || ('Already attended by ' + d.state.attended_by + '.'), 'info');
        }
        return r;
      });
    });
  }

  function unattend(row) {
    return guarded(row, function () {
      return post(row.dataset.unattendUrl).then(function (r) {
        if (r.skipped) return r;
        var d = withFallback(r, false);
        if (d.state) applyState(row, d.state);
        window.showToast(r.message || (r.ok ? 'Marked as unattended.' : "Couldn't update the message. Try again."), r.ok ? 'success' : 'error');
        return r;
      });
    });
  }

  // ---- Detail dialog ----
  function waNumber(phone) {
    var digits = (phone || '').replace(/\D/g, '');
    if (digits.indexOf('00') === 0) return digits.slice(2);
    if (digits.charAt(0) === '0') return DEFAULT_COUNTRY_CODE + digits.slice(1);
    return digits;
  }

  function fillModalStatus() {
    if (!current) return;
    var attended = isAttended(current);
    var statusEl = $('msgModalStatus');
    var ago = current.dataset.attendedAgo;

    statusEl.dataset.state = attended ? 'attended' : 'unattended';
    statusEl.textContent = attended
      ? 'Attended by ' + attendedBy(current) + (ago ? ', ' + ago : '')
      : 'Not attended yet';

    // Mark as attended: only while nobody has attended it.
    // Mark as unattended: only for the person who attended it.
    setVisible($('msgBtnAttend'), !attended);
    setVisible($('msgBtnUnattend'), attended && isMine(current));
  }

  function openModal(row) {
    current = row;
    opener = row.querySelector('.msg-open');
    var d = row.dataset;

    $('msgModalName').textContent = d.name;
    $('msgModalReceived').textContent = 'Received ' + d.received;

    var email = $('msgModalEmail');
    email.textContent = d.email;
    email.href = 'mailto:' + d.email;

    var hasPhone = !!d.phone;
    setVisible($('msgModalPhoneRow'), hasPhone);
    if (hasPhone) {
      $('msgModalPhone').textContent = d.phone;
      $('msgModalPhone').href = 'tel:' + d.phone.replace(/[^\d+]/g, '');
    }

    $('msgModalService').textContent = d.service || 'General';
    $('msgModalBody').textContent = d.message;   // textContent keeps it safe

    $('msgReplyEmail').href = 'mailto:' + d.email + '?subject=' + encodeURIComponent('Re: Your enquiry');

    var wa = hasPhone ? waNumber(d.phone) : '';
    var waLink = $('msgReplyWhatsapp');
    setVisible(waLink, !!wa);   // no phone number, no WhatsApp button
    if (wa) waLink.href = 'https://wa.me/' + wa;
    else waLink.removeAttribute('href');   // never leave the previous person's number behind

    fillModalStatus();
    openDialog(modal);
  }

  // Runs for Esc, the close button, the backdrop and programmatic closes
  modal.addEventListener('close', function () {
    current = null;
    if (opener && opener.isConnected && !opener.closest('tr').hidden) opener.focus();
    opener = null;
  });
  $('msgModalClose').addEventListener('click', function () { closeDialog(modal); });

  // Open from a click on the row, or Enter/Space on its button (which also fires click)
  body.addEventListener('click', function (event) {
    var row = event.target.closest('tr.msg-row');
    if (row) openModal(row);
  });

  // Replying marks the message attended, then the link opens as normal.
  function onReplyClick() {
    if (current && !isAttended(current)) attend(current, true);
  }
  $('msgReplyEmail').addEventListener('click', onReplyClick);
  $('msgReplyWhatsapp').addEventListener('click', onReplyClick);

  // Disables the button and shows its spinner and busy text while `task` runs
  function runBusy(button, spinner, label, idleText, busyText, task) {
    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
    spinner.classList.remove('hidden');
    label.textContent = busyText;
    return task().finally(function () {
      button.disabled = false;
      button.removeAttribute('aria-busy');
      spinner.classList.add('hidden');
      label.textContent = idleText;
    });
  }

  // On success the row and counters are already updated, so the dialog closes.
  // It stays open when the request failed, or when someone else had attended
  // the message first, so the corrected status can be read.
  $('msgBtnAttend').addEventListener('click', function () {
    var row = current;
    if (!row || this.disabled) return;
    runBusy(this, $('msgAttendSpinner'), $('msgAttendLabel'), 'Mark as attended', 'Marking...', function () {
      return attend(row, false).then(function (r) {
        if (r.ok && r.data && r.data.state && r.data.state.attended_by_is_you) closeDialog(modal);
        return r;
      });
    });
  });

  $('msgBtnUnattend').addEventListener('click', function () {
    var row = current;
    if (!row || this.disabled) return;
    runBusy(this, $('msgUnattendSpinner'), $('msgUnattendLabel'), 'Mark as unattended', 'Updating...', function () {
      return unattend(row).then(function (r) {
        if (r.ok) closeDialog(modal);
        return r;
      });
    });
  });

  // ---- Delete ----
  var deleteRow = null;

  deleteModal.addEventListener('close', function () { deleteRow = null; });
  // Esc does nothing while the request is running
  deleteModal.addEventListener('cancel', function (event) { if (deleting) event.preventDefault(); });

  $('msgBtnDelete').addEventListener('click', function () {
    if (!current) return;
    deleteRow = current;
    $('msgDeleteName').textContent = current.dataset.name;
    openDialog(deleteModal);
  });
  $('msgDeleteCancel').addEventListener('click', function () { if (!deleting) closeDialog(deleteModal); });

  $('msgDeleteConfirm').addEventListener('click', function () {
    var row = deleteRow;
    if (!row || deleting) return;
    var button = this;
    deleting = true;
    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
    $('msgDeleteSpinner').classList.remove('hidden');
    $('msgDeleteLabel').textContent = 'Deleting...';

    post(row.dataset.deleteUrl).then(function (r) {
      deleting = false;
      button.disabled = false;
      button.removeAttribute('aria-busy');
      $('msgDeleteSpinner').classList.add('hidden');
      $('msgDeleteLabel').textContent = 'Delete message';

      if (!r.ok) {
        window.showToast(r.message || "Couldn't delete the message. Try again.", 'error');
        return;
      }
      counts.total -= 1;
      if (!isAttended(row)) counts.unattended -= 1;
      renderCounts();
      opener = null;           // the row is going away, so focus is placed by hand below
      row.remove();
      closeDialog(deleteModal);
      closeDialog(modal);
      applyFilter(false);
      var next = body.querySelector('tr.msg-row:not([hidden]) .msg-open');
      (next || $('msgSearch')).focus();
      window.showToast(r.message || 'Message deleted.', 'success');
    });
  });

  // ---- Load more ----
  var moreBtn = $('msgMoreBtn');
  moreBtn.addEventListener('click', function () {
    var spinner = $('msgMoreSpinner');
    var label = $('msgMoreLabel');
    $('msgMoreError').hidden = true;
    moreBtn.disabled = true;
    moreBtn.setAttribute('aria-busy', 'true');
    spinner.classList.remove('hidden');
    label.textContent = 'Loading messages...';

    fetch(BATCH_URL_TEMPLATE.replace('123456789', moreBtn.dataset.next), {
      headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },
      credentials: 'same-origin'
    })
      .then(function (response) {
        if (!response.ok) throw new Error('bad status');
        return response.json();
      })
      .then(function (data) {
        body.insertAdjacentHTML('beforeend', data.html || '');
        moreBtn.dataset.next = data.next_batch_point;
        $('msgMoreWrap').hidden = !data.has_more;
        label.textContent = 'Load more';
        applyFilter(false);
      })
      .catch(function () {
        $('msgMoreError').hidden = false;
        label.textContent = 'Try again';
      })
      .finally(function () {
        moreBtn.disabled = false;
        moreBtn.removeAttribute('aria-busy');
        spinner.classList.add('hidden');
      });
  });
})();

function setActiveMsgTab(filter) {
  document.querySelectorAll('#msgTabs .msg-tab').forEach((t) => {
    const on = t.dataset.filter === filter;
    t.setAttribute('aria-pressed', String(on));
    t.classList.toggle('is-active', on);
  });
}

// Keeps the is-active class (the .seg-btn shade) in step with aria-pressed
(function syncMsgTabShade() {
  const tabs = document.getElementById('msgTabs');
  if (!tabs) return;

  function sync() {
    tabs.querySelectorAll('.msg-tab').forEach((t) => {
      t.classList.toggle('is-active', t.getAttribute('aria-pressed') === 'true');
    });
  }

  sync(); // set the starting shade from the initial aria-pressed
  new MutationObserver(sync).observe(tabs, {
    attributes: true,
    attributeFilter: ['aria-pressed'],
    subtree: true,
  });
})();