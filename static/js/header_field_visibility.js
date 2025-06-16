// Toggle visibility of header fields (title, id, dates)

document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('toggle-header-fields');
  const popover   = document.getElementById('header-field-popover');
  if (!toggleBtn || !popover) return;

  const elements = {
    title: document.getElementById('record-title'),
    id: document.getElementById('record-id'),
    date_added: document.getElementById('record-date-added'),
    last_edited: document.getElementById('record-last-edited'),
    separator: document.getElementById('record-date-separator')
  };

  function updateSeparator() {
    if (!elements.separator) return;
    const show = !elements.date_added?.classList.contains('hidden') &&
                 !elements.last_edited?.classList.contains('hidden');
    elements.separator.classList.toggle('hidden', !show);
  }

  function updateVisibility() {
    popover.querySelectorAll('.header-field-toggle').forEach(cb => {
      const el = elements[cb.value];
      if (el) el.classList.toggle('hidden', !cb.checked);
    });
    updateSeparator();
  }

  toggleBtn.addEventListener('click', e => {
    e.stopPropagation();
    popover.classList.toggle('hidden');
  });

  document.addEventListener('click', () => popover.classList.add('hidden'));
  popover.addEventListener('click', e => e.stopPropagation());

  popover.querySelectorAll('.header-field-toggle').forEach(cb => {
    cb.addEventListener('change', updateVisibility);
  });

  updateVisibility();
});
