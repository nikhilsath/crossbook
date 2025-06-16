import { initValueWidgets, createValueWidget, updateColumnOptions } from './dashboard_modal/value.js';
import { initTableWidgets, createTableWidget, updateTablePreview } from './dashboard_modal/table.js';
import { initChartWidgets, createChartWidget, updateChartUI } from './dashboard_modal/chart.js';

let dashboardTrigger = null;
const escHandler = (e) => {
  if (e.key === 'Escape') {
    closeDashboardModal();
  }
};

export function openDashboardModal() {
  dashboardTrigger = document.activeElement;
  document.getElementById('dashboardModal').classList.remove('hidden');
  document.addEventListener('keydown', escHandler);
}

export function closeDashboardModal() {
  document.getElementById('dashboardModal').classList.add('hidden');
  document.removeEventListener('keydown', escHandler);
  if (dashboardTrigger) {
    dashboardTrigger.focus();
    dashboardTrigger = null;
  }
}

let activeTab = 'value';

function setActiveTab(name) {
  activeTab = name;
  updateColumnOptions();
  if (activeTab === 'table') updateTablePreview();
  if (activeTab === 'chart') updateChartUI();
}

function initDashboardTabs() {
  ['value', 'table', 'chart'].forEach(name => {
    const tabEl = document.getElementById(`tab-${name}`);
    if (tabEl) {
      tabEl.addEventListener('click', () => setActiveTab(name));
    }
  });
}

function initDashboardModal() {
  initDashboardTabs();
  initValueWidgets();
  initTableWidgets();
  initChartWidgets();

  const createBtnEl = document.getElementById('dashboardCreateBtn');
  if (createBtnEl) {
    createBtnEl.addEventListener('click', async (e) => {
      e.preventDefault();
      const success = await createValueWidget();
      if (success) {
        closeDashboardModal();
        window.location.reload();
      }
    });
  }

  const tableCreateBtnEl = document.getElementById('tableCreateBtn');
  if (tableCreateBtnEl) {
    tableCreateBtnEl.addEventListener('click', async (e) => {
      e.preventDefault();
      const success = await createTableWidget();
      if (success) {
        closeDashboardModal();
        window.location.reload();
      }
    });
  }

  const chartCreateBtnEl = document.getElementById('chartCreateBtn');
  if (chartCreateBtnEl) {
    chartCreateBtnEl.addEventListener('click', async (e) => {
      e.preventDefault();
      const success = await createChartWidget();
      if (success) {
        closeDashboardModal();
        window.location.reload();
      }
    });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDashboardModal);
} else {
  initDashboardModal();
}

window.openDashboardModal = openDashboardModal;
window.closeDashboardModal = closeDashboardModal;
