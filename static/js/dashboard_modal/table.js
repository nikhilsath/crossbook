/**
 * Table widget preview helpers for the dashboard modal.
 */

import { populateFieldDropdown } from './value.js';

export let tableType = 'base-count';
export let selectCountField = null;
export let topNumericField = null;
export let topDirection = 'desc';
export let filteredTable = null;
export let filteredSearch = '';
export let filteredSort = null;
export let filteredLimit = 10;
export let tableData = [];

let tableTitleInputEl, tableCreateBtnEl, tablePreviewEl, tablePreviewBodyEl, tablePreviewHeaderEl;
let selectCountToggleBtn, selectCountToggleLabel, selectCountOptions, selectCountFieldContainer;
let topFieldToggleBtn, topFieldToggleLabel, topFieldOptions, topFieldContainer, topDirectionContainer;
let filteredTableToggleBtn, filteredTableToggleLabel, filteredTableOptions;
let filteredSortToggleBtn, filteredSortToggleLabel, filteredSortOptions;
let filteredSearchInputEl, filteredLimitInputEl, filteredRecordsContainer;

export function initTableWidgets() {
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
      input.className = 'rounded border-gray-300 text-teal-600 shadow-sm focus:ring-teal-500';
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

  updateTablePreview();

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
      input.className = 'rounded border-gray-300 text-teal-600 shadow-sm focus:ring-teal-500';
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
}

function getLabelField(table) {
  const schema = FIELD_SCHEMA[table] || {};
  const fields = Object.keys(schema);
  if (!fields.length) return null;
  if (fields.includes(table)) return table;
  return fields.length > 1 ? fields[1] : fields[0];
}

export function updateTablePreview() {
  if (!tablePreviewEl || !tablePreviewBodyEl || !tableTitleInputEl || !tableCreateBtnEl) return;
  tablePreviewBodyEl.innerHTML = '';
  tablePreviewEl.classList.add('hidden');
  tableTitleInputEl.classList.add('hidden');
  tableCreateBtnEl.classList.add('hidden');
  if (selectCountToggleBtn) selectCountToggleBtn.classList.add('hidden');
  if (selectCountOptions) selectCountOptions.classList.add('hidden');
  if (selectCountFieldContainer) selectCountFieldContainer.classList.add('hidden');
  if (topFieldToggleBtn) topFieldToggleBtn.classList.add('hidden');
  if (topFieldOptions) topFieldOptions.classList.add('hidden');
  if (topFieldContainer) topFieldContainer.classList.add('hidden');
  if (topDirectionContainer) topDirectionContainer.classList.add('hidden');
  if (filteredRecordsContainer) filteredRecordsContainer.classList.add('hidden');
  if (tableType === 'base-count') {
    if (tablePreviewHeaderEl)
      tablePreviewHeaderEl.innerHTML = '<th class="px-2 py-1 text-left">Table</th><th class="px-2 py-1 text-left">Count</th>';
    fetch('/dashboard/base-count')
      .then(r => r.json())
      .then(rows => {
        tableData = rows || [];
        tableData.forEach(r => {
          const tr = document.createElement('tr');
          tr.innerHTML = `<td class="px-2 py-1">${r.table}</td><td class="px-2 py-1">${r.count}</td>`;
          tablePreviewBodyEl.appendChild(tr);
        });
        tablePreviewEl.classList.remove('hidden');
        tableTitleInputEl.placeholder = 'Base Table Counts';
        tableTitleInputEl.value = 'Base Table Counts';
        tableTitleInputEl.classList.remove('hidden');
        tableCreateBtnEl.classList.remove('hidden');
      })
      .catch(() => {
        tableData = [];
        tablePreviewBodyEl.innerHTML = '<tr><td colspan="2" class="px-2 py-1">Error</td></tr>';
        tablePreviewEl.classList.remove('hidden');
      });
  } else if (tableType === 'select-count') {
    if (selectCountToggleBtn) selectCountToggleBtn.classList.remove('hidden');
    if (!selectCountField) {
      if (selectCountFieldContainer) selectCountFieldContainer.classList.remove('hidden');
      return;
    }
    if (selectCountFieldContainer) selectCountFieldContainer.classList.remove('hidden');
    const [tbl, fld] = selectCountField.split(':');
    if (tablePreviewHeaderEl)
      tablePreviewHeaderEl.innerHTML = '<th class="px-2 py-1 text-left">Value</th><th class="px-2 py-1 text-left">Count</th>';
    fetch(`/${tbl}/field-distribution?field=${encodeURIComponent(fld)}`)
      .then(r => r.json())
      .then(data => {
        tableData = Object.entries(data).map(([value, count]) => ({ value, count }));
        tableData.forEach(r => {
          const tr = document.createElement('tr');
          tr.innerHTML = `<td class="px-2 py-1">${r.value}</td><td class="px-2 py-1">${r.count}</td>`;
          tablePreviewBodyEl.appendChild(tr);
        });
        tablePreviewEl.classList.remove('hidden');
        const fieldLabel = fld;
        tableTitleInputEl.placeholder = `Value Counts for ${fieldLabel}`;
        tableTitleInputEl.value = `Value Counts for ${fieldLabel}`;
        tableTitleInputEl.classList.remove('hidden');
        tableCreateBtnEl.classList.remove('hidden');
      })
      .catch(() => {
        tableData = [];
        tablePreviewBodyEl.innerHTML = '<tr><td colspan="2" class="px-2 py-1">Error</td></tr>';
        tablePreviewEl.classList.remove('hidden');
      });
  } else if (tableType === 'top-numeric') {
    if (topFieldToggleBtn) topFieldToggleBtn.classList.remove('hidden');
    if (!topNumericField) {
      if (topFieldContainer) topFieldContainer.classList.remove('hidden');
      if (topDirectionContainer) topDirectionContainer.classList.remove('hidden');
      return;
    }
    if (topFieldContainer) topFieldContainer.classList.remove('hidden');
    if (topDirectionContainer) topDirectionContainer.classList.remove('hidden');
    const [tbl, fld] = topNumericField.split(':');
    if (tablePreviewHeaderEl)
      tablePreviewHeaderEl.innerHTML = '<th class="px-2 py-1 text-left">ID</th><th class="px-2 py-1 text-left">Value</th>';
    fetch(`/dashboard/top-numeric?table=${encodeURIComponent(tbl)}&field=${encodeURIComponent(fld)}&direction=${topDirection}&limit=5`)
      .then(r => r.json())
      .then(rows => {
        tableData = rows || [];
        tableData.forEach(r => {
          const tr = document.createElement('tr');
          tr.innerHTML = `<td class="px-2 py-1"><a href="/${tbl}/${r.id}" class="text-teal-600 underline">${r.id}</a></td><td class="px-2 py-1">${r.value}</td>`;
          tablePreviewBodyEl.appendChild(tr);
        });
        tablePreviewEl.classList.remove('hidden');
        const prefix = topDirection === 'desc' ? 'Top' : 'Bottom';
        tableTitleInputEl.placeholder = `${prefix} ${tableData.length} of ${fld}`;
        tableTitleInputEl.value = `${prefix} ${tableData.length} of ${fld}`;
        tableTitleInputEl.classList.remove('hidden');
        tableCreateBtnEl.classList.remove('hidden');
      })
      .catch(() => {
        tableData = [];
        tablePreviewBodyEl.innerHTML = '<tr><td colspan="2" class="px-2 py-1">Error</td></tr>';
        tablePreviewEl.classList.remove('hidden');
      });
  } else if (tableType === 'filtered-records') {
    if (!filteredTable) {
      if (filteredRecordsContainer) filteredRecordsContainer.classList.remove('hidden');
      return;
    }
    if (filteredRecordsContainer) filteredRecordsContainer.classList.remove('hidden');
    const labelField = getLabelField(filteredTable);
    if (tablePreviewHeaderEl)
      tablePreviewHeaderEl.innerHTML = `<th class="px-2 py-1 text-left">ID</th><th class="px-2 py-1 text-left">${labelField || 'Label'}</th>`;
    const params = new URLSearchParams({
      table: filteredTable,
      search: filteredSearch || '',
      order_by: filteredSort || '',
      limit: filteredLimit || 10
    });
    fetch(`/dashboard/filtered-records?${params.toString()}`)
      .then(r => r.json())
      .then(rows => {
        tableData = rows || [];
        tableData.forEach(r => {
          const tr = document.createElement('tr');
          const label = r[labelField];
          tr.innerHTML = `<td class="px-2 py-1"><a href="/${filteredTable}/${r.id}" class="text-teal-600 underline">${r.id}</a></td><td class="px-2 py-1">${label ?? ''}</td>`;
          tablePreviewBodyEl.appendChild(tr);
        });
        tablePreviewEl.classList.remove('hidden');
        tableTitleInputEl.placeholder = `Filtered ${filteredTable}`;
        tableTitleInputEl.value = `Filtered ${filteredTable}`;
        tableTitleInputEl.classList.remove('hidden');
        tableCreateBtnEl.classList.remove('hidden');
      })
      .catch(() => {
        tableData = [];
        tablePreviewBodyEl.innerHTML = '<tr><td colspan="2" class="px-2 py-1">Error</td></tr>';
        tablePreviewEl.classList.remove('hidden');
      });
  }
}

export async function createTableWidget() {
  if (!tableData.length) return false;
  if (tableType === 'select-count' && !selectCountField) return false;
  if (tableType === 'top-numeric' && !topNumericField) return false;
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
    row_span: 8,
    group: window.DASHBOARD_VIEW || 'Dashboard'
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
