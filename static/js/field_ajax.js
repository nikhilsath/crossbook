export function submitFieldAjax(formEl) {
  const statusEl = formEl.querySelector('.ajax-status');
  if (statusEl) {
    statusEl.textContent = 'Saving…';
    statusEl.classList.remove('hidden');
  }
  fetch(formEl.action, {
    method: formEl.method || 'POST',
    headers: { 'X-Requested-With': 'XMLHttpRequest' },
    body: new FormData(formEl)
  })
    .then(resp => {
      if (!resp.ok) throw new Error('Network response was not ok');
      if (statusEl) {
        statusEl.textContent = 'Saved';
        setTimeout(() => statusEl.classList.add('hidden'), 2000);
      }
    })
    .catch(() => {
      if (statusEl) {
        statusEl.textContent = 'Error';
        setTimeout(() => statusEl.classList.add('hidden'), 2000);
      }
    });
}
window.submitFieldAjax = submitFieldAjax;
