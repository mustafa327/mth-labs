/* No dependencies, trackers, storage, or form backend. */
(() => {
  'use strict';
  const EMAIL = 'mustafathaear97@gmail.com';
  const $ = (selector) => document.querySelector(selector);
  const menu = $('.menu-toggle');
  const nav = $('#navigation');
  function closeMenu() {
    if (!menu || !nav) return;
    menu.setAttribute('aria-expanded', 'false');
    nav.classList.remove('is-open');
  }
  menu?.addEventListener('click', () => {
    const open = menu.getAttribute('aria-expanded') !== 'true';
    menu.setAttribute('aria-expanded', String(open));
    nav?.classList.toggle('is-open', open);
  });
  nav?.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeMenu));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && menu?.getAttribute('aria-expanded') === 'true') {
      closeMenu();
      menu.focus();
    }
  });
  document.addEventListener('click', (event) => {
    if (nav && menu && !nav.contains(event.target) && !menu.contains(event.target)) closeMenu();
  });
  window.matchMedia('(min-width: 681px)').addEventListener('change', closeMenu);
  const year = $('#year');
  if (year) year.textContent = String(new Date().getFullYear());

  document.querySelectorAll('.service-choice').forEach((link) => {
    link.addEventListener('click', () => {
      const service = $('#service');
      if (service) service.value = link.dataset.service;
      const preview = $('#email-preview');
      if (preview) preview.hidden = true;
    });
  });

  async function copy(text, status, success) {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(text);
      status.textContent = success;
    } catch {
      status.textContent = 'Copy is unavailable in this browser. Select the email address or draft text and copy it manually.';
      const draft = $('#draft-text');
      if (draft && !$('#email-preview').hidden && text.includes('Subject:')) {
        draft.focus();
        draft.select();
      }
    }
  }
  $('.copy-email')?.addEventListener('click', () => copy(EMAIL, $('#copy-status'), 'Email address copied.'));

  const form = $('#project-form');
  const preview = $('#email-preview');
  let currentDraft = '';
  function line(value) { return String(value || '').trim().replace(/[\r\n]+/g, ' '); }
  form?.addEventListener('submit', (event) => {
    event.preventDefault();
    const nameField = $('#name');
    nameField.setCustomValidity(nameField.value.trim() ? '' : 'Please enter your name.');
    const message = $('#message');
    message.setCustomValidity(message.value.trim().length < 20 ? 'Please describe your project in at least 20 characters.' : '');
    if (!form.reportValidity()) return;
    const data = new FormData(form);
    const name = line(data.get('name'));
    const email = line(data.get('email'));
    const company = line(data.get('company'));
    const service = line(data.get('service'));
    const subject = `Project enquiry: ${service} — ${company || name}`;
    const body = [
      'Hello Mustafa,', '', 'I would like to discuss a project with MTH Labs.', '',
      `Name: ${name}`, `Email: ${email}`, `Company / project: ${company || 'Not specified'}`,
      `Service: ${service}`, `Budget: ${line(data.get('budget'))}`, `Timeline: ${line(data.get('timeline'))}`,
      '', 'Project outline:', String(data.get('message')).trim(), '', `Best regards,`, name
    ].join('\n');
    currentDraft = `To: ${EMAIL}\nSubject: ${subject}\n\n${body}`;
    $('#draft-text').value = currentDraft;
    $('#open-email').href = `mailto:${EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    $('#open-gmail').href = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(EMAIL)}&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    $('#draft-status').textContent = 'Your email is prepared, not sent. If an email link does not work, copy the draft or download it.';
    preview.hidden = false;
    $('#preview-title').focus({ preventScroll: true });
    preview.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'nearest' });
  });
  $('#name')?.addEventListener('input', (event) => event.target.setCustomValidity(''));
  $('#message')?.addEventListener('input', (event) => event.target.setCustomValidity(''));
  form?.addEventListener('input', () => { if (preview) preview.hidden = true; });
  form?.addEventListener('change', () => { if (preview) preview.hidden = true; });
  $('#copy-draft')?.addEventListener('click', () => copy(currentDraft, $('#draft-status'), 'Project email copied. Paste it into your email app and send it to Mustafa.'));
  $('#download-draft')?.addEventListener('click', () => {
    if (!currentDraft) return;
    const blob = new Blob([currentDraft], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'mth-labs-project-enquiry.txt';
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    $('#draft-status').textContent = 'Download requested. The draft is a text file; it has not been sent.';
  });
})();
