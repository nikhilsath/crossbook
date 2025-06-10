export function openDashboardModal() {
  document.getElementById('dashboardModal').classList.remove('hidden');
}

export function closeDashboardModal() {
  document.getElementById('dashboardModal').classList.add('hidden');
}

let selectedOperation = null;
let selectedColumn = null;
let columnContainer, columnToggleBtn, columnDropdown, valueResultEl;
let activeTab = 'value';

function setActiveTab(name) {
  activeTab = name;
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
  updateColumnOptions();
}

function initDashboardTabs() {
  ['value', 'table', 'chart'].forEach(name => {
    const tabEl = document.getElementById(`tab-${name}`);
    if (tabEl) {
      tabEl.addEventListener('click', () => setActiveTab(name));
    }
  });
}

function refreshColumnTags() {
  if (!columnContainer) return;
  columnContainer.innerHTML = '';
  if (!selectedColumn) return;

  const values = Array.isArray(selectedColumn) ? selectedColumn : [selectedColumn];
  values.forEach(val => {
    const [table, field] = val.split(':');
    const span = document.createElement('span');
    span.className = 'inline-flex items-center bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full';
    span.innerHTML = `<strong>${table}</strong>: ${field}`;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'ml-1 text-blue-500 hover:text-red-500';
    btn.textContent = '×';
    btn.addEventListener('click', () => {
      const input = columnDropdown.querySelector(`input[value="${val}"]`);
      if (input) input.checked = false;
      if (Array.isArray(selectedColumn)) {
        selectedColumn = selectedColumn.filter(v => v !== val);
      } else {
        selectedColumn = null;
      }
      refreshColumnTags();
    });
    span.appendChild(btn);
    columnContainer.appendChild(span);
  });
  updateValueResult();
}

function updateValueResult() {
  if (!valueResultEl) return;
  if (selectedOperation === 'sum' && selectedColumn) {
    const [table, field] = selectedColumn.split(':');
    valueResultEl.classList.remove('hidden');
    valueResultEl.textContent = 'Calculating…';
    fetch(`/${table}/sum-field?field=${encodeURIComponent(field)}`)
      .then(res => res.json())
      .then(data => {
        valueResultEl.textContent = `Sum: ${data.sum}`;
      })
      .catch(() => {
        valueResultEl.textContent = 'Error';
      });
  } else {
    valueResultEl.classList.add('hidden');
    valueResultEl.textContent = '';
  }
}

function updateColumnOptions() {
  if (!columnDropdown || !columnToggleBtn) return;

  if (!selectedOperation) {
    columnToggleBtn.classList.add('hidden');
    columnDropdown.classList.add('hidden');
    selectedColumn = null;
    refreshColumnTags();
    return;
  }

  columnToggleBtn.classList.remove('hidden');
  columnDropdown.innerHTML = '';

  const inputType = selectedOperation === 'math' ? 'checkbox' : 'radio';

  if (selectedOperation === 'math' && !Array.isArray(selectedColumn)) {
    selectedColumn = [];
  }
  if (selectedOperation !== 'math' && Array.isArray(selectedColumn)) {
    selectedColumn = selectedColumn[0] || null;
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

  Object.keys(FIELD_SCHEMA).forEach(table => {
    const fields = FIELD_SCHEMA[table] ? Object.keys(FIELD_SCHEMA[table]) : [];
    fields.forEach(field => {
      const type = FIELD_SCHEMA[table] && FIELD_SCHEMA[table][field] ? FIELD_SCHEMA[table][field].type : '';
      if (selectedOperation === 'sum' && type !== 'number') return;
      const val = `${table}:${field}`;
      const label = document.createElement('label');
      label.className = 'flex items-center space-x-2';
      const input = document.createElement('input');
      input.type = inputType;
      input.name = 'columnSelect';
      input.value = val;
      input.className = 'rounded border-gray-300 text-blue-600 shadow-sm focus:ring-blue-500';

      if (inputType === 'checkbox') {
        if (selectedColumn.includes(val)) input.checked = true;
        input.addEventListener('change', () => {
          if (input.checked) {
            if (!selectedColumn.includes(val)) selectedColumn.push(val);
          } else {
            selectedColumn = selectedColumn.filter(v => v !== val);
          }
          refreshColumnTags();
        });
      } else {
        if (selectedColumn === val) input.checked = true;
        input.addEventListener('change', () => {
          selectedColumn = val;
          refreshColumnTags();
        });
      }

      const span = document.createElement('span');
      span.className = 'text-sm';
      span.innerHTML = `<strong>${table}</strong>: ${field} <span class="text-blue-600 text-xs">(${type})</span>`;
      label.appendChild(input);
      label.appendChild(span);
      columnDropdown.appendChild(label);
    });
  });

  refreshColumnTags();
  updateValueResult();
}

function initColumnSelect() {
  columnContainer = document.getElementById('selectedColumns');
  columnToggleBtn = document.getElementById('columnSelectDashboardToggle');
  columnDropdown = document.getElementById('columnSelectDashboardOptions');
  if (!columnContainer || !columnToggleBtn || !columnDropdown) return;

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

  updateColumnOptions();
}

function initOperationSelect() {
  const opSelect = document.getElementById('dashboardOperation');
  if (!opSelect) return;
  opSelect.addEventListener('change', () => {
    const checked = opSelect.querySelector('input[name="dashboardOperation"]:checked');
    selectedOperation = checked ? checked.value : null;
    selectedColumn = selectedOperation === 'math' ? [] : null;
    updateColumnOptions();
  });
}

function initDashboardModal() {
  initDashboardTabs();
  initOperationSelect();
  initColumnSelect();
  valueResultEl = document.getElementById('valueResult');
}

document.addEventListener('DOMContentLoaded', initDashboardModal);

window.openDashboardModal = openDashboardModal;
window.closeDashboardModal = closeDashboardModal;

