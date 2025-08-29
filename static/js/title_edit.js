export function initTitleInlineEdit() {
  const titleEl = document.getElementById('record-title');
  if (!titleEl || !titleEl.dataset.field) return;
  if (titleEl.dataset.readonly === '1' || titleEl.dataset.readonly === 'true') return;

  let original = '';

  titleEl.addEventListener('dblclick', () => {
    if (titleEl.dataset.readonly === '1' || titleEl.dataset.readonly === 'true') return;
    if (titleEl.getAttribute('contenteditable') === 'true') return;
    original = titleEl.innerText.trim();
    titleEl.setAttribute('contenteditable', 'true');
    titleEl.focus();
    const range = document.createRange();
    range.selectNodeContents(titleEl);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  });

  titleEl.addEventListener('blur', async () => {
    if (titleEl.getAttribute('contenteditable') !== 'true') return;
    titleEl.setAttribute('contenteditable', 'false');
    const newValue = titleEl.innerText.trim();
    if (newValue === original) return;
    const data = new FormData();
    data.append('field', titleEl.dataset.field);
    data.append('new_value', newValue);
    try {
      await fetch(`/${titleEl.dataset.table}/${titleEl.dataset.recordId}/update`, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: data
      });
    } catch (err) {
      console.error('Title update failed', err);
      titleEl.innerText = original;
    }
  });
}

document.addEventListener('DOMContentLoaded', initTitleInlineEdit);
