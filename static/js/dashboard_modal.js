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

function initTableSelect() {
  const container = document.getElementById('selectedTables');
  const toggleBtn = document.getElementById('tableSelectToggle');
  const dropdown = document.getElementById('tableSelectOptions');
  if (!container || !toggleBtn || !dropdown) return;

  const checkboxes = dropdown.querySelectorAll('input[type="checkbox"]');

  function refreshTags() {
    container.innerHTML = '';
    checkboxes.forEach(cb => {
      if (cb.checked) {
        const span = document.createElement('span');
        span.className = 'inline-flex items-center bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full';
        span.textContent = cb.value;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'ml-1 text-blue-500 hover:text-red-500';
        btn.textContent = '×';
        btn.addEventListener('click', () => {
          cb.checked = false;
          refreshTags();
        });
        span.appendChild(btn);
        container.appendChild(span);
      }
    });
  }

  toggleBtn.addEventListener('click', e => {
    e.stopPropagation();
    dropdown.classList.toggle('hidden');
  });

  document.addEventListener('click', e => {
    if (!dropdown.contains(e.target) && e.target !== toggleBtn) {
      dropdown.classList.add('hidden');
    }
  });

  dropdown.addEventListener('click', e => e.stopPropagation());

  checkboxes.forEach(cb => cb.addEventListener('change', refreshTags));

  refreshTags();
}

function initDashboardModal() {
  initDashboardTabs();
  initTableSelect();
}

document.addEventListener('DOMContentLoaded', initDashboardModal);

window.openDashboardModal = openDashboardModal;
window.closeDashboardModal = closeDashboardModal;

