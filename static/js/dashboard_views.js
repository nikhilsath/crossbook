export function initDashboardViews() {
  const select = document.getElementById('dashboardViewSelect');
  const addBtn = document.getElementById('addDashboardView');

  function updateVisibility() {
    const view = select ? select.value : 'Dashboard';
    window.DASHBOARD_VIEW = view;
    document.querySelectorAll('#dashboard-grid .dashboard-widget').forEach(el => {
      el.classList.toggle('hidden', el.dataset.group !== view);
    });
  }

  if (select) {
    select.addEventListener('change', updateVisibility);
  }
  if (addBtn && select) {
    addBtn.addEventListener('click', () => {
      const name = prompt('View name:');
      if (!name) return;
      const opt = document.createElement('option');
      opt.value = name;
      opt.textContent = name;
      select.appendChild(opt);
      select.value = name;
      updateVisibility();
    });
  }
  updateVisibility();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDashboardViews);
} else {
  initDashboardViews();
}
