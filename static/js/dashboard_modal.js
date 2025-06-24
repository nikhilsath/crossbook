import { initValueWidgets, createValueWidget, updateColumnOptions } from './dashboard_modal/value.js';
import { initTableWidgets, createTableWidget, updateTablePreview } from './dashboard_modal/table.js';
import { initChartWidgets, createChartWidget, updateChartUI } from './dashboard_modal/chart.js';
import { openModal, closeModal } from './modal_helper.js';

export function openDashboardModal() {
  openModal('dashboardModal');
  setActiveTab('value');
}

export function closeDashboardModal() {
  closeModal('dashboardModal');
}

let activeTab = 'value';

function setActiveTab(name) {
  activeTab = name;
  ['value', 'table', 'chart'].forEach(n => {
    const pane = document.getElementById(`pane-${n}`);
    const tab = document.getElementById(`tab-${n}`);
    if (pane) pane.classList.toggle('hidden', n !== name);
    if (tab) {
      const active = n === name;
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
      tab.classList.toggle('text-primary', active);
      tab.classList.toggle('border-primary', active);
      tab.classList.toggle('border-transparent', !active);
      tab.classList.toggle('hover:text-gray-600', !active);
      tab.classList.toggle('hover:border-gray-300', !active);
    }
  });
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
  setActiveTab(activeTab);

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
