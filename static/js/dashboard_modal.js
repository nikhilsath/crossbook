import { updateAggToggleUI, updateAverageButtonUI, updateMathFieldUI, refreshColumnTags, updateValueResult, populateFieldDropdown, updateColumnOptions, initColumnSelect, initOperationSelect } from "./value_widgets.js";
import { updateTablePreview } from "./table_widgets.js";

let dashboardTrigger = null;
let escHandler = (e) => {
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
let mathField1Container, mathField2Container;
let aggToggle1El, aggToggle2El;
let valueResultEl, titleInputEl, resultRowEl, createBtnEl, mathOpContainer;
let activeTab = 'value';
let chartTypeEl,
    chartXToggleBtn, chartXLabel, chartXOptions,
    chartYToggleBtn, chartYLabel, chartYOptions,
    chartAggToggleEl, chartTitleInputEl, chartCreateBtnEl,
    chartXFieldContainer, chartYFieldContainer, chartAggContainer,
    chartXFieldLabel, chartOrientContainer;
let chartXField = null;
let chartYField = null;
let chartAgg = '';
let chartOrient = 'x';
let tableType = 'base-count';
let selectCountField = null;
let selectCountToggleBtn, selectCountToggleLabel, selectCountOptions, selectCountFieldContainer;
let topNumericField = null;
let topDirection = 'desc';
let topFieldToggleBtn, topFieldToggleLabel, topFieldOptions, topFieldContainer, topDirectionContainer;
let filteredTable = null;
let filteredSearch = '';
let filteredSort = null;
let filteredLimit = 10;
let filteredTableToggleBtn, filteredTableToggleLabel, filteredTableOptions;
let filteredSortToggleBtn, filteredSortToggleLabel, filteredSortOptions;
let filteredSearchInputEl, filteredLimitInputEl, filteredRecordsContainer;
let tableTitleInputEl, tableCreateBtnEl, tablePreviewEl, tablePreviewBodyEl, tablePreviewHeaderEl;
let tableData = [];


function getNonTextTypes() {
  const types = new Set();
  Object.values(FIELD_SCHEMA).forEach(tbl => {
    Object.values(tbl).forEach(meta => types.add(meta.type));
  });
  return Array.from(types).filter(t => t !== 'text' && t !== 'textarea' && t !== 'url');
}


function updateChartUI() {
  if (!chartTypeEl || !chartXFieldContainer || !chartYFieldContainer || !chartAggContainer || !chartOrientContainer || !chartTitleInputEl || !chartCreateBtnEl) return;
  const type = chartTypeEl.value;
  chartXFieldContainer.classList.add('hidden');
  chartYFieldContainer.classList.add('hidden');
  chartAggContainer.classList.add('hidden');
  chartOrientContainer.classList.add('hidden');
  chartTitleInputEl.classList.add('hidden');
  chartCreateBtnEl.classList.add('hidden');
  chartXFieldLabel.textContent = 'X Field';
  if (!type) return;
  chartXFieldContainer.classList.remove('hidden');
  chartTitleInputEl.classList.remove('hidden');
  chartCreateBtnEl.classList.remove('hidden');
  if (type === 'pie') {
    chartXFieldLabel.textContent = 'Category Field';
    populateFieldDropdown(chartXOptions, false, ['select', 'multi_select'], val => {
      chartXField = val;
      if (chartXLabel) {
        const [t,f] = val.split(':');
        chartXLabel.textContent = `${t}: ${f}`;
      }
      updateChartTitle();
    });
  } else if (type === 'bar') {
    chartXFieldLabel.textContent = 'Field';
    populateFieldDropdown(chartXOptions, false, getNonTextTypes(), val => {
      chartXField = val;
      if (chartXLabel) {
        const [t,f] = val.split(':');
        chartXLabel.textContent = `${t}: ${f}`;
      }
      updateChartTitle();
    }, ['text', 'textarea']);
    chartOrientContainer.classList.remove('hidden');
  } else if (type === 'line') {
    chartXFieldLabel.textContent = 'Field';
    // Line charts only support sequential numeric or date fields
    populateFieldDropdown(chartXOptions, false, ['number', 'date'], val => {
      chartXField = val;
      if (chartXLabel) {
        const [t,f] = val.split(':');
        chartXLabel.textContent = `${t}: ${f}`;
      }
      updateChartTitle();
    });
  } else {
    chartXFieldLabel.textContent = 'X Field';
    populateFieldDropdown(chartXOptions, false, null, val => {
      chartXField = val;
      if (chartXLabel) {
        const [t,f] = val.split(':');
        chartXLabel.textContent = `${t}: ${f}`;
      }
      updateChartTitle();
    });
    chartYFieldContainer.classList.remove('hidden');
    chartAggContainer.classList.remove('hidden');
  }
  updateChartTitle();
}

function updateChartTitle() {
  if (!chartTitleInputEl) return;
  const type = chartTypeEl ? chartTypeEl.value : '';
  if (!type) return;
  let field = chartXField || chartYField;
  if (!field) return;
  const fieldName = field.split(':')[1];
  const typeCap = type.charAt(0).toUpperCase() + type.slice(1);
  const defaultTitle = `${typeCap} Chart of ${fieldName}`;
  chartTitleInputEl.placeholder = defaultTitle;
  chartTitleInputEl.value = defaultTitle;
}


function setActiveTab(name) {
  activeTab = name;
  updateColumnOptions();
  if (activeTab === 'table') updateTablePreview();
}

function initDashboardTabs() {
  ['value', 'table', 'chart'].forEach(name => {
    const tabEl = document.getElementById(`tab-${name}`);
    if (tabEl) {
      tabEl.addEventListener('click', () => setActiveTab(name));
    }
  });
}


function onCreateWidget(event) {
  if (event) event.preventDefault();

  if (activeTab === 'table') {
    if (!tableData.length) return;
    if (tableType === 'select-count' && !selectCountField) return;
    if (tableType === 'top-numeric' && !topNumericField) return;
    const title = (tableTitleInputEl && tableTitleInputEl.value.trim()) || 'Table Widget';
    const payloadContent = { type: tableType, data: tableData };
    if (tableType === 'select-count' && selectCountField) {
      const [tbl, fld] = selectCountField.split(':');
      payloadContent.table = tbl;
      payloadContent.field = fld;
    } else if (tableType === 'top-numeric' && topNumericField) {
      const [tbl, fld] = topNumericField.split(':');
      payloadContent.table = tbl;
      payloadContent.field = fld;
      payloadContent.direction = topDirection;
      payloadContent.limit = tableData.length;
    } else if (tableType === 'filtered-records' && filteredTable) {
      payloadContent.table = filteredTable;
      payloadContent.search = filteredSearch || '';
      payloadContent.order_by = filteredSort || '';
      payloadContent.limit = filteredLimit || tableData.length;
    }
    const payload = {
      title,
      content: JSON.stringify(payloadContent),
      widget_type: 'table',
      col_start: 1,
      col_span: 10,
      row_start: 1,
      row_span: 8
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
      .catch(() => { console.error('Failed to create widget'); });
    return;
  }

  // Chart widget
  if (activeTab === 'chart') {
    const chartType = chartTypeEl ? chartTypeEl.value : '';
    const aggInput = chartAggToggleEl ? chartAggToggleEl.querySelector('input[name="chartAgg"]:checked') : null;
    chartAgg = aggInput ? aggInput.value : '';
    let payloadContent;
    if (chartType === 'pie') {
      if (!chartXField) return;
      payloadContent = {
        chart_type: chartType,
        x_field: chartXField
      };
    } else if (chartType === 'bar') {
      if (!chartXField) return;
      payloadContent = {
        chart_type: chartType,
        field: chartXField,
        orientation: chartOrient
      };
    } else if (chartType === 'line') {
      if (!chartXField) return;
      payloadContent = {
        chart_type: chartType,
        field: chartXField
      };
    } else {
      if (!chartXField || !chartYField) return;
      payloadContent = {
        chart_type: chartType,
        x_field: chartXField,
        y_field: chartYField,
        aggregation: chartAgg
      };
    }
    const title = (chartTitleInputEl && chartTitleInputEl.value.trim()) || 'Chart Widget';
    const payload = {
      title,
      content: JSON.stringify(payloadContent),
      widget_type: 'chart',
      col_start: 1,
      col_span: 10,
      row_start: 1,
      row_span: 12
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
    return;
  }

  // Value widget
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
  mathField1Container = document.getElementById('mathField1');
  mathField2Container = document.getElementById('mathField2');
  chartTypeEl = document.getElementById('chartTypeSelect');
  chartXToggleBtn = document.getElementById('chartXFieldToggle');
  chartXLabel = chartXToggleBtn ? chartXToggleBtn.querySelector('.selected-label') : null;
  chartXOptions = document.getElementById('chartXFieldOptions');
  chartYToggleBtn = document.getElementById('chartYFieldToggle');
  chartYLabel = chartYToggleBtn ? chartYToggleBtn.querySelector('.selected-label') : null;
  chartYOptions = document.getElementById('chartYFieldOptions');
  chartXFieldContainer = document.getElementById('chartXFieldContainer');
  chartYFieldContainer = document.getElementById('chartYFieldContainer');
  chartAggContainer = document.getElementById('chartAggContainer');
  chartXFieldLabel = document.getElementById('chartXFieldLabel');
  chartOrientContainer = document.getElementById('chartOrientContainer');
  chartAggToggleEl = document.getElementById('chartAggToggle');
  chartTitleInputEl = document.getElementById('chartTitleInput');
  chartCreateBtnEl = document.getElementById('chartCreateBtn');
  tableTitleInputEl = document.getElementById('tableTitleInput');
  tableCreateBtnEl = document.getElementById('tableCreateBtn');
  tablePreviewEl = document.getElementById('tablePreview');
  tablePreviewBodyEl = document.getElementById('tablePreviewBody');
  tablePreviewHeaderEl = document.getElementById('tablePreviewHeader');
  selectCountToggleBtn = document.getElementById('selectCountFieldToggle');
  selectCountToggleLabel = selectCountToggleBtn ? selectCountToggleBtn.querySelector('.selected-label') : null;
  selectCountOptions = document.getElementById('selectCountFieldOptions');
  selectCountFieldContainer = document.getElementById('selectCountFieldContainer');
  topFieldToggleBtn = document.getElementById('topNumericFieldToggle');
  topFieldToggleLabel = topFieldToggleBtn ? topFieldToggleBtn.querySelector('.selected-label') : null;
  topFieldOptions = document.getElementById('topNumericFieldOptions');
  topFieldContainer = document.getElementById('topNumericFieldContainer');
  topDirectionContainer = document.getElementById('topNumericDirection');
  filteredRecordsContainer = document.getElementById('filteredRecordsContainer');
  filteredTableToggleBtn = document.getElementById('filteredTableToggle');
  filteredTableToggleLabel = filteredTableToggleBtn ? filteredTableToggleBtn.querySelector('.selected-label') : null;
  filteredTableOptions = document.getElementById('filteredTableOptions');
  filteredSearchInputEl = document.getElementById('filteredSearchInput');
  filteredSortToggleBtn = document.getElementById('filteredSortToggle');
  filteredSortToggleLabel = filteredSortToggleBtn ? filteredSortToggleBtn.querySelector('.selected-label') : null;
  filteredSortOptions = document.getElementById('filteredSortOptions');
  filteredLimitInputEl = document.getElementById('filteredLimitInput');
  const tableTypeSelect = document.getElementById('tableTypeSelect');
  if (tableTypeSelect) {
    tableTypeSelect.addEventListener('change', () => {
      const checked = tableTypeSelect.querySelector('input[name="tableType"]:checked');
      tableType = checked ? checked.value : 'base-count';
      updateTablePreview();
    });
  }
  if (selectCountToggleBtn && selectCountOptions) {
    selectCountToggleBtn.addEventListener('click', e => { e.stopPropagation(); selectCountOptions.classList.toggle('hidden'); });
    document.addEventListener('click', e => {
      if (!selectCountOptions.contains(e.target) && e.target !== selectCountToggleBtn) {
        selectCountOptions.classList.add('hidden');
      }
    });
    selectCountOptions.addEventListener('click', e => e.stopPropagation());
    populateFieldDropdown(selectCountOptions, false, ['select','multi_select'], val => {
      selectCountField = val;
      if (selectCountToggleLabel) {
        const [t,f] = val.split(':');
        selectCountToggleLabel.textContent = `${t}: ${f}`;
      }
      updateTablePreview();
    });
  }
  if (topFieldToggleBtn && topFieldOptions) {
    topFieldToggleBtn.addEventListener('click', e => { e.stopPropagation(); topFieldOptions.classList.toggle('hidden'); });
    document.addEventListener('click', e => {
      if (!topFieldOptions.contains(e.target) && e.target !== topFieldToggleBtn) {
        topFieldOptions.classList.add('hidden');
      }
    });
    topFieldOptions.addEventListener('click', e => e.stopPropagation());
    populateFieldDropdown(topFieldOptions, true, ['number'], val => {
      topNumericField = val;
      if (topFieldToggleLabel) {
        const [t,f] = val.split(':');
        topFieldToggleLabel.textContent = `${t}: ${f}`;
      }
      updateTablePreview();
    });
  }
  if (topDirectionContainer) {
    topDirectionContainer.addEventListener('change', () => {
      const checked = topDirectionContainer.querySelector('input[name="topDirection"]:checked');
      topDirection = checked ? checked.value : 'desc';
      updateTablePreview();
    });
  }
  if (filteredTableToggleBtn && filteredTableOptions) {
    filteredTableToggleBtn.addEventListener('click', e => { e.stopPropagation(); filteredTableOptions.classList.toggle('hidden'); });
    document.addEventListener('click', e => {
      if (!filteredTableOptions.contains(e.target) && e.target !== filteredTableToggleBtn) {
        filteredTableOptions.classList.add('hidden');
      }
    });
    filteredTableOptions.addEventListener('click', e => e.stopPropagation());
    filteredTableOptions.innerHTML = '';
    Object.keys(FIELD_SCHEMA).forEach(tbl => {
      const label = document.createElement('label');
      label.className = 'flex items-center space-x-2';
      const input = document.createElement('input');
      input.type = 'radio';
      input.name = 'filteredTable';
      input.value = tbl;
      input.className = 'rounded border-gray-300 text-blue-600 shadow-sm focus:ring-blue-500';
      input.addEventListener('change', () => {
        filteredTable = tbl;
        if (filteredTableToggleLabel) filteredTableToggleLabel.textContent = tbl;
        populateSortOptions();
        updateTablePreview();
        filteredTableOptions.classList.add('hidden');
      });
      const span = document.createElement('span');
      span.className = 'text-sm';
      span.textContent = tbl;
      label.appendChild(input); label.appendChild(span);
      filteredTableOptions.appendChild(label);
    });
  }
  function populateSortOptions() {
    if (!filteredSortOptions) return;
    filteredSortOptions.innerHTML = '';
    if (!filteredTable) return;
    Object.keys(FIELD_SCHEMA[filteredTable] || {}).forEach(fld => {
      const label = document.createElement('label');
      label.className = 'flex items-center space-x-2';
      const input = document.createElement('input');
      input.type = 'radio';
      input.name = 'filteredSort';
      input.value = fld;
      input.className = 'rounded border-gray-300 text-blue-600 shadow-sm focus:ring-blue-500';
      input.addEventListener('change', () => {
        filteredSort = fld;
        if (filteredSortToggleLabel) filteredSortToggleLabel.textContent = fld;
        filteredSortOptions.classList.add('hidden');
        updateTablePreview();
      });
      const span = document.createElement('span');
      span.className = 'text-sm';
      span.textContent = fld;
      label.appendChild(input); label.appendChild(span);
      filteredSortOptions.appendChild(label);
    });
  }
  if (filteredSortToggleBtn && filteredSortOptions) {
    filteredSortToggleBtn.addEventListener('click', e => { e.stopPropagation(); filteredSortOptions.classList.toggle('hidden'); });
    document.addEventListener('click', e => {
      if (!filteredSortOptions.contains(e.target) && e.target !== filteredSortToggleBtn) {
        filteredSortOptions.classList.add('hidden');
      }
    });
    filteredSortOptions.addEventListener('click', e => e.stopPropagation());
  }
  if (filteredSearchInputEl) {
    filteredSearchInputEl.addEventListener('input', e => { filteredSearch = e.target.value; updateTablePreview(); });
  }
  if (filteredLimitInputEl) {
    filteredLimitInputEl.addEventListener('input', e => { const v = parseInt(e.target.value, 10); filteredLimit = isNaN(v) ? 10 : v; updateTablePreview(); });
  }
  if (mathOpContainer) {
    mathOpContainer.addEventListener('change', () => {
      const checked = mathOpContainer.querySelector('input[name="mathOperation"]:checked');
      mathOperation = checked ? checked.value : null;
      updateMathFieldUI();
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
  if (chartXToggleBtn && chartXOptions) {
    chartXToggleBtn.addEventListener('click', e => { e.stopPropagation(); chartXOptions.classList.toggle('hidden'); });
    document.addEventListener('click', e => {
      if (!chartXOptions.contains(e.target) && e.target !== chartXToggleBtn) chartXOptions.classList.add('hidden');
    });
    chartXOptions.addEventListener('click', e => e.stopPropagation());
    populateFieldDropdown(chartXOptions, false, null, val => {
      chartXField = val;
      if (chartXLabel) {
        const [t,f] = val.split(':');
        chartXLabel.textContent = `${t}: ${f}`;
      }
      updateChartTitle();
    });
  }
  if (chartYToggleBtn && chartYOptions) {
    chartYToggleBtn.addEventListener('click', e => { e.stopPropagation(); chartYOptions.classList.toggle('hidden'); });
    document.addEventListener('click', e => {
      if (!chartYOptions.contains(e.target) && e.target !== chartYToggleBtn) chartYOptions.classList.add('hidden');
    });
    chartYOptions.addEventListener('click', e => e.stopPropagation());
    populateFieldDropdown(chartYOptions, false, null, val => {
      chartYField = val;
      if (chartYLabel) {
        const [t,f] = val.split(':');
        chartYLabel.textContent = `${t}: ${f}`;
      }
      updateChartTitle();
    });
  }
  if (chartAggToggleEl) {
    chartAggToggleEl.addEventListener('change', () => {
      const checked = chartAggToggleEl.querySelector('input[name="chartAgg"]:checked');
      chartAgg = checked ? checked.value : '';
    });
  }
  if (chartOrientContainer) {
    chartOrientContainer.addEventListener('change', () => {
      const checked = chartOrientContainer.querySelector('input[name="chartOrient"]:checked');
      chartOrient = checked ? checked.value : 'x';
    });
  }
  if (chartCreateBtnEl) {
    chartCreateBtnEl.addEventListener('click', onCreateWidget);
  }
  if (tableCreateBtnEl) {
    tableCreateBtnEl.addEventListener('click', onCreateWidget);
  }
  if (chartTypeEl) {
    chartTypeEl.addEventListener('change', updateChartUI);
  }

  updateAggToggleUI();
  updateAverageButtonUI();
  updateMathFieldUI();
  updateChartUI();
  updateTablePreview();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDashboardModal);
} else {
  initDashboardModal();
}

window.openDashboardModal = openDashboardModal;
window.closeDashboardModal = closeDashboardModal;

