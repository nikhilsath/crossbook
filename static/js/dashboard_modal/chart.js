import { populateFieldDropdown } from './value.js';

let chartTypeEl,
    chartXToggleBtn, chartXLabel, chartXOptions,
    chartYToggleBtn, chartYLabel, chartYOptions,
    chartAggToggleEl, chartTitleInputEl, chartCreateBtnEl,
    chartXFieldContainer, chartYFieldContainer, chartAggContainer,
    chartXFieldLabel, chartOrientContainer;

export let chartXField = null;
export let chartYField = null;
let chartAgg = '';
let chartOrient = 'x';

function getNonTextTypes() {
  const types = new Set();
  Object.values(FIELD_SCHEMA).forEach(tbl => {
    Object.values(tbl).forEach(meta => types.add(meta.type));
  });
  return Array.from(types).filter(t => t !== 'text' && t !== 'textarea' && t !== 'url');
}

export function updateChartUI() {
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

export function initChartWidgets() {
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
  if (chartTypeEl) {
    chartTypeEl.addEventListener('change', updateChartUI);
  }
  updateChartUI();
}

export async function createChartWidget() {
  const chartType = chartTypeEl ? chartTypeEl.value : '';
  const aggInput = chartAggToggleEl ? chartAggToggleEl.querySelector('input[name="chartAgg"]:checked') : null;
  chartAgg = aggInput ? aggInput.value : '';
  let payloadContent;
  if (chartType === 'pie') {
    if (!chartXField) return false;
    payloadContent = {
      chart_type: chartType,
      x_field: chartXField
    };
  } else if (chartType === 'bar') {
    if (!chartXField) return false;
    payloadContent = {
      chart_type: chartType,
      field: chartXField,
      orientation: chartOrient
    };
  } else if (chartType === 'line') {
    if (!chartXField) return false;
    payloadContent = {
      chart_type: chartType,
      field: chartXField
    };
  } else {
    if (!chartXField || !chartYField) return false;
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
  try {
    const res = await fetch('/dashboard/widget', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    return data.success;
  } catch (err) {
    console.error('Failed to create widget');
    return false;
  }
}
