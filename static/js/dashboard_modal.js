export function openDashboardModal() {
  document.getElementById('dashboardModal').classList.remove('hidden');
}

export function closeDashboardModal() {
  document.getElementById('dashboardModal').classList.add('hidden');
}

let selectedOperation = null;

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
  const selectEl = document.getElementById('columnSelectDashboard');
  if (!selectEl) return;

  selectEl.innerHTML = '<option value="" disabled selected>Select Field</option>';
  Object.keys(FIELD_SCHEMA).forEach(table => {
    const fields = FIELD_SCHEMA[table] ? Object.keys(FIELD_SCHEMA[table]) : [];
    fields.forEach(field => {
      const type = FIELD_SCHEMA[table][field] ? FIELD_SCHEMA[table][field].type : '';
      const opt = document.createElement('option');
      opt.value = `${table}:${field}`;
      opt.textContent = `${table}: ${field} (${type})`;
      selectEl.appendChild(opt);
    });
  });
}

function initOperationSelect() {
  const opSelect = document.getElementById('dashboardOperation');
  const columnSelect = document.getElementById('columnSelectDashboard');
  if (!opSelect) return;
  opSelect.addEventListener('change', () => {
    const checked = opSelect.querySelector('input[name="dashboardOperation"]:checked');
    selectedOperation = checked ? checked.value : null;
    if (columnSelect && selectedOperation) {
      columnSelect.classList.remove('hidden');
    }
  });
}

function initDashboardModal() {
  initDashboardTabs();
  initOperationSelect();
  initTableSelect();
}

document.addEventListener('DOMContentLoaded', initDashboardModal);

window.openDashboardModal = openDashboardModal;
window.closeDashboardModal = closeDashboardModal;

