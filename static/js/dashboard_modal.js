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
  const columnContainer = document.getElementById('selectedColumns');
  const columnToggleBtn = document.getElementById('columnSelectToggle');
  const columnDropdown = document.getElementById('columnSelectOptions');
  if (!container || !toggleBtn || !dropdown) return;

  const checkboxes = dropdown.querySelectorAll('input[type="checkbox"]');
  let selectedColumn = null;

  function refreshColumnTags() {
    if (!columnContainer || !columnDropdown) return;
    columnContainer.innerHTML = '';
    if (selectedColumn) {
      const [table, field] = selectedColumn.split(':');
      const span = document.createElement('span');
      span.className = 'inline-flex items-center bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full';
      span.innerHTML = `<strong>${table}</strong>: ${field}`;
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'ml-1 text-blue-500 hover:text-red-500';
      btn.textContent = '×';
      btn.addEventListener('click', () => {
        const cb = columnDropdown.querySelector(`input[value="${selectedColumn}"]`);
        if (cb) cb.checked = false;
        selectedColumn = null;
        refreshColumnTags();
      });
      span.appendChild(btn);
      columnContainer.appendChild(span);
    }
  }

  function updateColumnOptions() {
    if (!columnDropdown) return;
    const tables = Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);
    const valid = new Set();

    columnDropdown.innerHTML = '';
    if (tables.length === 0) {
      selectedColumn = null;
      refreshColumnTags();
      return;
    }

    const search = document.createElement('input');
    search.type = 'text';
    search.placeholder = 'Search...';
    search.className = 'w-full px-2 py-1 border rounded text-sm mb-2';
    search.addEventListener('input', function() {
      const v = this.value.toLowerCase();
      [...columnDropdown.querySelectorAll('label')].forEach(l => l.classList.toggle('hidden', !l.textContent.toLowerCase().includes(v)));
    });
    columnDropdown.appendChild(search);

    tables.forEach(table => {
      const fields = FIELD_SCHEMA[table] ? Object.keys(FIELD_SCHEMA[table]) : [];
      fields.forEach(field => {
        const val = `${table}:${field}`;
        valid.add(val);
        const label = document.createElement('label');
        label.className = 'flex items-center space-x-2';
        const input = document.createElement('input');
        input.type = 'radio';
        input.name = 'columnSelect';
        input.value = val;
        input.className = 'rounded border-gray-300 text-blue-600 shadow-sm focus:ring-blue-500';
        if (selectedColumn === val) input.checked = true;
        input.addEventListener('change', () => { selectedColumn = val; refreshColumnTags(); });
        const span = document.createElement('span');
        span.className = 'text-sm';
        span.innerHTML = `<strong>${table}</strong>: ${field}`;
        label.appendChild(input);
        label.appendChild(span);
        columnDropdown.appendChild(label);
      });
    });

    if (!valid.has(selectedColumn)) selectedColumn = null;
    refreshColumnTags();
  }

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
    updateColumnOptions();
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

  if (columnToggleBtn && columnDropdown) {
    columnToggleBtn.addEventListener('click', e => {
      e.stopPropagation();
      columnDropdown.classList.toggle('hidden');
    });
    document.addEventListener('click', e => {
      if (!columnDropdown.contains(e.target) && e.target !== columnToggleBtn) {
        columnDropdown.classList.add('hidden');
      }
    });
    columnDropdown.addEventListener('click', e => e.stopPropagation());
  }

  refreshTags();
}

function initDashboardModal() {
  initDashboardTabs();
  initTableSelect();
}

document.addEventListener('DOMContentLoaded', initDashboardModal);

window.openDashboardModal = openDashboardModal;
window.closeDashboardModal = closeDashboardModal;

