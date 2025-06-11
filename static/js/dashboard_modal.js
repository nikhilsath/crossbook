export function openDashboardModal() {
  document.getElementById('dashboardModal').classList.remove('hidden');
}

export function closeDashboardModal() {
  document.getElementById('dashboardModal').classList.add('hidden');
}

let selectedOperation = null;
let selectedColumn = null;
let mathOperation = null;
let mathField1 = null;
let mathField2 = null;
let agg1 = 'sum';
let agg2 = 'sum';
let columnToggleBtn, columnToggleLabel, columnDropdown;
let mathSelect1Btn, mathSelect1Label, mathSelect1Options;
let mathSelect2Btn, mathSelect2Label, mathSelect2Options;
let aggToggle1El, aggToggle2El;
let valueResultEl, titleInputEl, resultRowEl, createBtnEl, mathOpContainer;
let activeTab = 'value';

function isNumericField(val) {
  if (!val) return false;
  const [table, field] = val.split(':');
  return (
    FIELD_SCHEMA[table] &&
    FIELD_SCHEMA[table][field] &&
    FIELD_SCHEMA[table][field].type === 'number'
  );
}

function toggleDisabled(label, input, disabled) {
  if (!label || !input) return;
  input.disabled = disabled;
  if (disabled) {
    label.classList.add('opacity-50', 'pointer-events-none');
  } else {
    label.classList.remove('opacity-50', 'pointer-events-none');
  }
}

function updateAggToggleUI() {
  if (aggToggle1El) {
    const sumInput = aggToggle1El.querySelector('input[value="sum"]');
    const countInput = aggToggle1El.querySelector('input[value="count"]');
    const sumLabel = sumInput ? sumInput.parentElement : null;
    const numeric = isNumericField(mathField1);
    toggleDisabled(sumLabel, sumInput, !numeric);
    if (!numeric && sumInput && sumInput.checked && countInput) {
      countInput.checked = true;
      agg1 = 'count';
    }
  }
  if (aggToggle2El) {
    const sumInput = aggToggle2El.querySelector('input[value="sum"]');
    const countInput = aggToggle2El.querySelector('input[value="count"]');
    const sumLabel = sumInput ? sumInput.parentElement : null;
    const numeric = isNumericField(mathField2);
    toggleDisabled(sumLabel, sumInput, !numeric);
    if (!numeric && sumInput && sumInput.checked && countInput) {
      countInput.checked = true;
      agg2 = 'count';
    }
  }
}

function updateAverageButtonUI() {
  if (!mathOpContainer) return;
  const avgInput = mathOpContainer.querySelector('input[value="average"]');
  const avgLabel = avgInput ? avgInput.parentElement : null;
  const numeric = isNumericField(mathField1);
  toggleDisabled(avgLabel, avgInput, !numeric);
  if (!numeric && avgInput && avgInput.checked) {
    avgInput.checked = false;
    mathOperation = null;
  }
}

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
  if (!selectedColumn) {
    if (columnToggleLabel) columnToggleLabel.textContent = 'Select Field';
    updateValueResult();
    return;
  }

  const [table, field] = selectedColumn.split(':');
  if (columnToggleLabel) columnToggleLabel.textContent = `${table}: ${field}`;

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
  } else if (selectedOperation === 'math' && mathField1 && mathOperation && (mathOperation === 'average' || mathField2)) {
    resultRowEl.classList.remove('hidden');
    if (createBtnEl) createBtnEl.classList.remove('hidden');
    const labels = [mathField1, mathOperation !== 'average' ? mathField2 : null].filter(Boolean).map(v => v.split(':')[1]);
    const defaultTitle = `${mathOperation.charAt(0).toUpperCase() + mathOperation.slice(1)} of ${labels.join(', ')}`;
    if (titleInputEl) {
      titleInputEl.placeholder = defaultTitle;
      titleInputEl.value = defaultTitle;
    }
    valueResultEl.textContent = 'Calculating…';
    if (mathOperation === 'average') {
      const [table, field] = mathField1.split(':');
      Promise.all([
        fetch(`/${table}/sum-field?field=${encodeURIComponent(field)}`).then(r => r.json()).then(d => d.sum || 0).catch(() => 0),
        fetch(`/${table}/count-nonnull?field=${encodeURIComponent(field)}`).then(r => r.json()).then(d => d.count || 1).catch(() => 1)
      ])
      .then(([s, c]) => { valueResultEl.textContent = c ? s / c : 0; })
      .catch(() => { valueResultEl.textContent = 'Error'; });
    } else {
      const fields = [
        { val: mathField1, mode: agg1 },
        { val: mathField2, mode: agg2 }
      ];
      Promise.all(fields.map(f => {
        const [table, field] = f.val.split(':');
        const endpoint = f.mode === 'sum' ? 'sum-field' : 'count-nonnull';
        const key = f.mode === 'sum' ? 'sum' : 'count';
        return fetch(`/${table}/${endpoint}?field=${encodeURIComponent(field)}`)
          .then(res => res.json())
          .then(d => d[key] || 0)
          .catch(() => 0);
      }))
      .then(nums => {
        let result = 0;
        if (mathOperation === 'add') result = nums[0] + nums[1];
        else if (mathOperation === 'subtract') result = nums[0] - nums[1];
        else if (mathOperation === 'multiply') result = nums[0] * nums[1];
        else if (mathOperation === 'divide') result = nums[0] / (nums[1] || 1);
        valueResultEl.textContent = result;
      })
      .catch(() => { valueResultEl.textContent = 'Error'; });
    }
  } else {
    resultRowEl.classList.add('hidden');
    valueResultEl.textContent = '';
    if (createBtnEl) createBtnEl.classList.add('hidden');
  }
}

function onCreateWidget(event) {
  if (event) event.preventDefault();
  if (selectedOperation === 'math') {
    if (!mathField1 || !mathOperation || (mathOperation !== 'average' && !mathField2)) return;
  } else if (!['sum', 'count'].includes(selectedOperation) || !selectedColumn) {
    return;
  }

  let defaultTitle;
  let payloadContent;

  if (selectedOperation === 'math') {
    const labels = [mathField1, mathOperation !== 'average' ? mathField2 : null].filter(Boolean).map(v => v.split(':')[1]);
    defaultTitle = `${mathOperation.charAt(0).toUpperCase() + mathOperation.slice(1)} of ${labels.join(', ')}`;
    payloadContent = { operation: 'math', math_operation: mathOperation, field1: mathField1, field2: mathField2, agg1, agg2 };
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

function populateFieldDropdown(dropdown, restrictNumeric, callback) {
  if (!dropdown) return;
  dropdown.innerHTML = '';
  const search = document.createElement('input');
  search.type = 'text';
  search.placeholder = 'Search...';
  search.className = 'w-full px-2 py-1 border rounded text-sm mb-2';
  search.addEventListener('input', function() {
    const v = this.value.toLowerCase();
    [...dropdown.querySelectorAll('label')].forEach(l => l.classList.toggle('hidden', !l.textContent.toLowerCase().includes(v)));
  });
  dropdown.appendChild(search);

  Object.keys(FIELD_SCHEMA).forEach(table => {
    const tableSchema = FIELD_SCHEMA[table] || {};
    const fields = Object.keys(tableSchema);
    fields.forEach(field => {
      const type = tableSchema[field] ? tableSchema[field].type : '';
      if (restrictNumeric && type !== 'number') return;
      const val = `${table}:${field}`;
      const label = document.createElement('label');
      label.className = 'flex items-center space-x-2';
      const input = document.createElement('input');
      input.type = 'radio';
      input.name = 'fieldSelect';
      input.value = val;
      input.className = 'rounded border-gray-300 text-blue-600 shadow-sm focus:ring-blue-500';
      input.addEventListener('change', () => {
        callback(val);
        dropdown.classList.add('hidden');
      });
      const span = document.createElement('span');
      span.className = 'text-sm';
      span.innerHTML = `<strong>${table}</strong>: ${field} <span class="text-blue-600 text-xs">(${type})</span>`;
      label.appendChild(input);
      label.appendChild(span);
      dropdown.appendChild(label);
    });
  });
}

function updateColumnOptions() {
  if (!columnToggleBtn || !columnDropdown) return;

  // hide everything first
  columnToggleBtn.classList.add('hidden');
  columnDropdown.classList.add('hidden');
  if (mathSelect1Btn) mathSelect1Btn.parentElement.parentElement.classList.add('hidden');
  if (mathSelect2Btn) mathSelect2Btn.parentElement.parentElement.classList.add('hidden');
  if (mathOpContainer) mathOpContainer.classList.add('hidden');

  if (!selectedOperation) {
    selectedColumn = null;
    mathField1 = null;
    mathField2 = null;
    mathOperation = null;
    updateAggToggleUI();
    updateAverageButtonUI();
    updateValueResult();
    return;
  }

  if (selectedOperation === 'sum' || selectedOperation === 'count') {
    columnToggleBtn.classList.remove('hidden');
    populateFieldDropdown(columnDropdown, selectedOperation === 'sum', val => {
      selectedColumn = val;
      refreshColumnTags();
    });
    refreshColumnTags();
  } else if (selectedOperation === 'math') {
    if (mathSelect1Btn) mathSelect1Btn.parentElement.parentElement.classList.remove('hidden');
    if (mathOpContainer) mathOpContainer.classList.remove('hidden');
    populateFieldDropdown(mathSelect1Options, false, val => {
      mathField1 = val;
      if (mathSelect1Label) {
        const [t,f] = val.split(':');
        mathSelect1Label.textContent = `${t}: ${f}`;
      }
      updateAggToggleUI();
      updateAverageButtonUI();
      updateValueResult();
    });
    populateFieldDropdown(mathSelect2Options, false, val => {
      mathField2 = val;
      if (mathSelect2Label) {
        const [t,f] = val.split(':');
        mathSelect2Label.textContent = `${t}: ${f}`;
      }
      updateAggToggleUI();
      updateValueResult();
    });
  }

  updateAggToggleUI();
  updateAverageButtonUI();
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
    selectedColumn = null;
    mathField1 = null;
    mathField2 = null;
    mathOperation = null;
    updateColumnOptions();
  });
}

function initDashboardModal() {
  initDashboardTabs();
  initOperationSelect();
  initColumnSelect();
  mathSelect1Btn = document.getElementById('mathSelect1Toggle');
  mathSelect1Label = mathSelect1Btn ? mathSelect1Btn.querySelector('.selected-label') : null;
  mathSelect1Options = document.getElementById('mathSelect1Options');
  mathSelect2Btn = document.getElementById('mathSelect2Toggle');
  mathSelect2Label = mathSelect2Btn ? mathSelect2Btn.querySelector('.selected-label') : null;
  mathSelect2Options = document.getElementById('mathSelect2Options');
  aggToggle1El = document.getElementById('aggToggle1');
  aggToggle2El = document.getElementById('aggToggle2');
  valueResultEl = document.getElementById('valueResult');
  titleInputEl = document.getElementById('valueTitleInput');
  resultRowEl = document.getElementById('resultRow');
  createBtnEl = document.getElementById('dashboardCreateBtn');
  mathOpContainer = document.getElementById('mathOperationContainer');
  if (mathOpContainer) {
    mathOpContainer.addEventListener('change', () => {
      const checked = mathOpContainer.querySelector('input[name="mathOperation"]:checked');
      mathOperation = checked ? checked.value : null;
      updateValueResult();
    });
  }
  if (mathSelect1Btn && mathSelect1Options) {
    mathSelect1Btn.addEventListener('click', e => { e.stopPropagation(); mathSelect1Options.classList.toggle('hidden'); });
    document.addEventListener('click', e => {
      if (!mathSelect1Options.contains(e.target) && e.target !== mathSelect1Btn) mathSelect1Options.classList.add('hidden');
    });
    mathSelect1Options.addEventListener('click', e => e.stopPropagation());
  }
  if (mathSelect2Btn && mathSelect2Options) {
    mathSelect2Btn.addEventListener('click', e => { e.stopPropagation(); mathSelect2Options.classList.toggle('hidden'); });
    document.addEventListener('click', e => {
      if (!mathSelect2Options.contains(e.target) && e.target !== mathSelect2Btn) mathSelect2Options.classList.add('hidden');
    });
    mathSelect2Options.addEventListener('click', e => e.stopPropagation());
  }
  if (aggToggle1El) {
    aggToggle1El.addEventListener('change', () => {
      const checked = aggToggle1El.querySelector('input[name="agg1"]:checked');
      agg1 = checked ? checked.value : 'sum';
      updateValueResult();
    });
  }
  if (aggToggle2El) {
    aggToggle2El.addEventListener('change', () => {
      const checked = aggToggle2El.querySelector('input[name="agg2"]:checked');
      agg2 = checked ? checked.value : 'sum';
      updateValueResult();
    });
  }
  if (createBtnEl) {
    createBtnEl.addEventListener('click', onCreateWidget);
  }

  updateAggToggleUI();
  updateAverageButtonUI();
}

document.addEventListener('DOMContentLoaded', initDashboardModal);

window.openDashboardModal = openDashboardModal;
window.closeDashboardModal = closeDashboardModal;

