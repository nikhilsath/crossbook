export function submitFieldAjax(formEl) {
  const statusEl = formEl.querySelector('.ajax-status');
  if (statusEl) {
    statusEl.textContent = 'Saving…';
    statusEl.classList.remove('hidden');
  }
  return fetch(formEl.action, {
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
      return resp;
    })
    .catch(err => {
      if (statusEl) {
        statusEl.textContent = 'Error';
        setTimeout(() => statusEl.classList.add('hidden'), 2000);
      }
      throw err;
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

// Autosave handler for multi_select checkboxes
export function submitMultiSelectAuto(formEl) {
  const formData = new FormData(formEl);
  fetch(formEl.action, {
    method: 'POST',
    headers: { 'X-Requested-With': 'XMLHttpRequest' },
    body: formData
  })
    .then(resp => {
      if (!resp.ok) throw new Error('Network response was not ok');
      updateSelectedTagsDOM(formEl);
    })
    .catch(err => console.error('submitMultiSelectAuto failed', err));
}

function updateSelectedTagsDOM(formEl) {
  const container = formEl.querySelector('div.flex.flex-wrap');
  if (!container) return;
  container.innerHTML = '';
  const checkboxes = formEl.querySelectorAll('input[name="new_value[]"]');
  checkboxes.forEach(cb => {
    if (cb.checked) {
      const span = document.createElement('span');
      span.className = 'inline-flex items-center bg-teal-100 text-teal-700 text-xs px-2 py-1 rounded-full';
      span.textContent = cb.value;
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'ml-1 text-teal-600 hover:text-red-500';
      btn.textContent = '×';
      btn.onclick = () => {
        cb.checked = false;
        submitMultiSelectAuto(formEl);
      };
      span.appendChild(btn);
      container.appendChild(span);
    }
  });
}

window.submitMultiSelectAuto = submitMultiSelectAuto;
