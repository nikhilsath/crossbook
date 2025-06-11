export function openDashboardModal() {
  document.getElementById('dashboardModal').classList.remove('hidden');
}

export function closeDashboardModal() {
  document.getElementById('dashboardModal').classList.add('hidden');
}

let selectedOperation = null;
let selectedColumn = null;
let mathOperation = null;
let columnToggleBtn, columnToggleLabel, columnDropdown, valueResultEl, titleInputEl, resultRowEl, createBtnEl, mathTagsContainer, mathOpContainer;
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
  if (!columnToggleBtn) return;
  if (!selectedColumn || (Array.isArray(selectedColumn) && selectedColumn.length === 0)) {
    if (columnToggleLabel) columnToggleLabel.textContent = 'Select Field';
    if (mathTagsContainer) mathTagsContainer.innerHTML = '';
    updateValueResult();
    return;
  }

  const values = Array.isArray(selectedColumn) ? selectedColumn : [selectedColumn];
  const labels = values.map(val => {
    const [table, field] = val.split(':');
    return `${table}: ${field}`;
  });

  if (columnToggleLabel) columnToggleLabel.textContent = labels.join(', ');

  if (selectedOperation === 'math' && mathTagsContainer) {
    mathTagsContainer.innerHTML = '';
    values.forEach(val => {
      const [table, field] = val.split(':');
      const tag = document.createElement('span');
      tag.className = 'inline-flex items-center bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full';
      tag.textContent = `${table}: ${field}`;
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'ml-1 text-blue-500 hover:text-red-500';
      btn.textContent = '×';
      btn.onclick = () => {
        selectedColumn = selectedColumn.filter(v => v !== val);
        const cb = columnDropdown.querySelector(`input[value="${val}"]`);
        if (cb) cb.checked = false;
        refreshColumnTags();
      };
      tag.appendChild(btn);
      mathTagsContainer.appendChild(tag);
    });
  } else if (mathTagsContainer) {
    mathTagsContainer.innerHTML = '';
  }

  updateValueResult();
}

function updateValueResult() {
  if (!valueResultEl || !resultRowEl) return;
  if ((selectedOperation === 'sum' || selectedOperation === 'count') && selectedColumn) {
    const [table, field] = selectedColumn.split(':');
    const endpoint = selectedOperation === 'sum' ? 'sum-field' : 'count-nonnull';
    const key = selectedOperation === 'sum' ? 'sum' : 'count';
    resultRowEl.classList.remove('hidden');
    if (titleInputEl) {
      const defaultTitle = `${selectedOperation === 'sum' ? 'Sum' : 'Count'} of ${field}`;
      titleInputEl.placeholder = defaultTitle;
      titleInputEl.value = defaultTitle;
    }
    if (createBtnEl) createBtnEl.classList.remove('hidden');
    valueResultEl.textContent = 'Calculating…';
    fetch(`/${table}/${endpoint}?field=${encodeURIComponent(field)}`)
      .then(res => res.json())
      .then(data => {
        valueResultEl.textContent = data[key];
      })
      .catch(() => {
        valueResultEl.textContent = 'Error';
      });
  } else if (selectedOperation === 'math' && Array.isArray(selectedColumn) && selectedColumn.length >= 2 && mathOperation) {
    resultRowEl.classList.remove('hidden');
    if (createBtnEl) createBtnEl.classList.remove('hidden');
    const labels = selectedColumn.map(val => val.split(':')[1]);
    const defaultTitle = `${mathOperation.charAt(0).toUpperCase() + mathOperation.slice(1)} of ${labels.join(', ')}`;
    if (titleInputEl) {
      titleInputEl.placeholder = defaultTitle;
      titleInputEl.value = defaultTitle;
    }
    valueResultEl.textContent = 'Calculating…';
    Promise.all(selectedColumn.map(val => {
      const [table, field] = val.split(':');
      return fetch(`/${table}/sum-field?field=${encodeURIComponent(field)}`)
        .then(res => res.json())
        .then(d => d.sum || 0)
        .catch(() => 0);
    }))
    .then(nums => {
      let result = nums[0] || 0;
      for (let i = 1; i < nums.length; i++) {
        const n = nums[i] || 0;
        if (mathOperation === 'add') result += n;
        else if (mathOperation === 'subtract') result -= n;
        else if (mathOperation === 'multiply') result *= n;
        else if (mathOperation === 'divide') result /= n || 1;
      }
      valueResultEl.textContent = result;
    })
    .catch(() => {
      valueResultEl.textContent = 'Error';
    });
  } else {
    resultRowEl.classList.add('hidden');
    valueResultEl.textContent = '';
    if (createBtnEl) createBtnEl.classList.add('hidden');
  }
}

function onCreateWidget(event) {
  if (event) event.preventDefault();
  if (selectedOperation === 'math') {
    if (!Array.isArray(selectedColumn) || selectedColumn.length < 2 || !mathOperation) return;
  } else if (!['sum', 'count'].includes(selectedOperation) || !selectedColumn) {
    return;
  }

  let defaultTitle;
  let payloadContent;

  if (selectedOperation === 'math') {
    const labels = selectedColumn.map(val => val.split(':')[1]);
    defaultTitle = `${mathOperation.charAt(0).toUpperCase() + mathOperation.slice(1)} of ${labels.join(', ')}`;
    payloadContent = { operation: 'math', math_operation: mathOperation, columns: selectedColumn };
  } else {
    const [table, field] = selectedColumn.split(':');
    defaultTitle = `${selectedOperation === 'sum' ? 'Sum' : 'Count'} of ${field}`;
    payloadContent = { operation: selectedOperation, table, field };
  }

  const title = (titleInputEl && titleInputEl.value.trim()) || defaultTitle;
  const payload = {
    title: title,
    content: JSON.stringify(payloadContent),
    widget_type: 'value',
    col_start: 1,
    col_span: 4,
    row_start: 1,
    row_span: 3
  };
  fetch('/dashboard/widget', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        closeDashboardModal();
        window.location.reload();
      }
    })
    .catch(() => {
      console.error('Failed to create widget');
    });
}

function updateColumnOptions() {
  if (!columnDropdown || !columnToggleBtn) return;

  if (!selectedOperation) {
    columnToggleBtn.classList.add('hidden');
    columnDropdown.classList.add('hidden');
    selectedColumn = null;
    if (mathTagsContainer) {
      mathTagsContainer.classList.add('hidden');
      mathTagsContainer.innerHTML = '';
    }
    if (mathOpContainer) {
      mathOpContainer.classList.add('hidden');
      const checked = mathOpContainer.querySelector('input[name="mathOperation"]:checked');
      if (checked) checked.checked = false;
      mathOperation = null;
    }
    refreshColumnTags();
    return;
  }

  columnToggleBtn.classList.remove('hidden');
  columnDropdown.innerHTML = '';
  if (mathTagsContainer) {
    if (selectedOperation === 'math') {
      mathTagsContainer.classList.remove('hidden');
      if (mathOpContainer) mathOpContainer.classList.remove('hidden');
    } else {
      mathTagsContainer.classList.add('hidden');
      mathTagsContainer.innerHTML = '';
      if (mathOpContainer) {
        mathOpContainer.classList.add('hidden');
        const checked = mathOpContainer.querySelector('input[name="mathOperation"]:checked');
        if (checked) checked.checked = false;
        mathOperation = null;
      }
    }
  }

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
          columnDropdown.classList.add('hidden');
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
  columnToggleBtn = document.getElementById('columnSelectDashboardToggle');
  columnToggleLabel = columnToggleBtn ? columnToggleBtn.querySelector('.selected-label') : null;
  columnDropdown = document.getElementById('columnSelectDashboardOptions');
  if (!columnToggleBtn || !columnDropdown) return;

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
  titleInputEl = document.getElementById('valueTitleInput');
  resultRowEl = document.getElementById('resultRow');
  createBtnEl = document.getElementById('dashboardCreateBtn');
  mathTagsContainer = document.getElementById('mathTagsContainer');
  mathOpContainer = document.getElementById('mathOperationContainer');
  if (mathOpContainer) {
    mathOpContainer.addEventListener('change', () => {
      const checked = mathOpContainer.querySelector('input[name="mathOperation"]:checked');
      mathOperation = checked ? checked.value : null;
      updateValueResult();
    });
  }
  if (createBtnEl) {
    createBtnEl.addEventListener('click', onCreateWidget);
  }
}

document.addEventListener('DOMContentLoaded', initDashboardModal);

window.openDashboardModal = openDashboardModal;
window.closeDashboardModal = closeDashboardModal;

