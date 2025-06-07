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

export function toggleBooleanAjax(formEl) {
  const statusEl = formEl.querySelector('.ajax-status');
  const btn = formEl.querySelector('button');
  const hidden = formEl.querySelector('input[name="new_value_override"]');
  const newVal = hidden.value;
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
      const isTrue = newVal === '1' || newVal === 1 || newVal === true;
      btn.classList.toggle('bg-green-500', isTrue);
      btn.classList.toggle('bg-red-500', !isTrue);
      const dot = btn.querySelector('span:nth-of-type(2)');
      if (dot) {
        dot.classList.toggle('translate-x-5', isTrue);
        dot.classList.toggle('translate-x-1', !isTrue);
      }
      hidden.value = isTrue ? '0' : '1';
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
window.toggleBooleanAjax = toggleBooleanAjax;
