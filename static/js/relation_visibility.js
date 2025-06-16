// Toggle visibility of related record sections

document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('toggle-relation-visibility');
  const pop = document.getElementById('relation-visibility-popover');
  if (!btn || !pop) return;

  const table = btn.dataset.table;
  let config = window.RELATION_VISIBILITY || {};

  function sendConfig() {
    fetch(`/${table}/relationships`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ visibility: config })
    }).catch(() => {});
  }

  function updateSection(section) {
    const settings = config[section] || {};
    const hidden = settings.hidden;
    const force = settings.force;
    document.querySelectorAll(`li.related-group[data-section="${section}"]`).forEach(el => {
      const hasItems = parseInt(el.dataset.hasItems, 10) > 0;
      const hide = hidden && (force || !hasItems);
      el.classList.toggle('hidden', hide);
    });
  }

  function initCheckboxes() {
    pop.querySelectorAll('.relation-visible').forEach(cb => {
      const sec = cb.value;
      cb.checked = !(config[sec] && config[sec].hidden);
      cb.addEventListener('change', () => {
        config[sec] = config[sec] || {};
        config[sec].hidden = !cb.checked;
        sendConfig();
        updateSection(sec);
      });
    });
    pop.querySelectorAll('.relation-force').forEach(cb => {
      const sec = cb.dataset.section;
      cb.checked = !!(config[sec] && config[sec].force);
      cb.addEventListener('change', () => {
        config[sec] = config[sec] || {};
        config[sec].force = cb.checked;
        sendConfig();
        updateSection(sec);
      });
    });
  }

  btn.addEventListener('click', e => {
    e.stopPropagation();
    pop.classList.toggle('hidden');
  });
  document.addEventListener('click', () => pop.classList.add('hidden'));
  pop.addEventListener('click', e => e.stopPropagation());

  initCheckboxes();
  Object.keys(config).forEach(updateSection);
});
