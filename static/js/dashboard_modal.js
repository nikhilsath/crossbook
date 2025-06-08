export function openDashboardModal() {
  document.getElementById('dashboardModal').classList.remove('hidden');
}

export function closeDashboardModal() {
  document.getElementById('dashboardModal').classList.add('hidden');
}

function setActiveTab(name) {
  const tabs = ['value', 'table', 'chart'];
  const colorMap = {
    value: ['border-blue-600', 'text-blue-600'],
    table: ['border-purple-600', 'text-purple-600'],
    chart: ['border-pink-600', 'text-pink-600']
  };

  tabs.forEach(tabName => {
    const tabEl = document.getElementById(`tab-${tabName}`);
    const paneEl = document.getElementById(`pane-${tabName}`);
    tabEl.classList.remove('border-blue-600', 'text-blue-600', 'border-purple-600', 'text-purple-600', 'border-pink-600', 'text-pink-600', 'border-transparent', 'text-gray-600');

    if (tabName === name) {
      tabEl.classList.add(...colorMap[tabName]);
      paneEl.classList.remove('hidden');
    } else {
      tabEl.classList.add('border-transparent', 'text-gray-600');
      paneEl.classList.add('hidden');
    }
  });
}

function initDashboardTabs() {
  ['value', 'table', 'chart'].forEach(name => {
    const tabEl = document.getElementById(`tab-${name}`);
    if (tabEl) {
      tabEl.addEventListener('click', () => setActiveTab(name));
    }
  });
}

document.addEventListener('DOMContentLoaded', initDashboardTabs);

window.openDashboardModal = openDashboardModal;
window.closeDashboardModal = closeDashboardModal;

