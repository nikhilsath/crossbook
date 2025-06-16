// Toggle visibility of header fields (title, id, dates)

document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('toggle-header-fields');
  const dropdown = document.getElementById('header-field-dropdown');
  const wrapper = document.getElementById('special-visibility-wrapper');
  if (!toggleBtn || !dropdown) return;

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
    dropdown.querySelectorAll('.header-field-toggle').forEach(cb => {
      const el = elements[cb.value];
      if (el) el.classList.toggle('hidden', !cb.checked);
    });
    updateSeparator();
  }

  toggleBtn.addEventListener('click', e => {
    e.stopPropagation();
    dropdown.classList.toggle('hidden');
  });

  document.addEventListener('click', () => dropdown.classList.add('hidden'));
  dropdown.addEventListener('click', e => e.stopPropagation());

  dropdown.querySelectorAll('.header-field-toggle').forEach(cb => {
    cb.addEventListener('change', updateVisibility);
  });

  updateVisibility();
});
