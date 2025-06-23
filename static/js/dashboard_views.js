import { openModal, closeModal } from './modal_helper.js';

export function initDashboardViews() {
  const select = document.getElementById('dashboardViewSelect');
  const addBtn = document.getElementById('addDashboardView');
  const form = document.getElementById('dashboardViewForm');
  const nameInput = document.getElementById('dashboardViewName');

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
  function addView(name) {
    const opt = document.createElement('option');
    opt.value = name;
    opt.textContent = name;
    select.appendChild(opt);
    select.value = name;
    updateVisibility();
  }

  if (addBtn && select && form && nameInput) {
    addBtn.addEventListener('click', () => {
      nameInput.value = '';
      openModal('dashboardViewModal');
    });

    form.addEventListener('submit', e => {
      e.preventDefault();
      const name = nameInput.value.trim();
      if (!name) {
        closeModal('dashboardViewModal');
        return;
      }
      addView(name);
      closeModal('dashboardViewModal');
    });
  }
  updateVisibility();
}


if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDashboardViews);
} else {
  initDashboardViews();
}
