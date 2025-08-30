let tables = [];
let currentTable = 0;
let addFieldTrigger = null;
let editingFieldIdx = null;

function showAddFieldModal(idx, fidx = null) {
  currentTable = idx;
  editingFieldIdx = fidx;
  addFieldTrigger = document.activeElement;
  const modal = document.getElementById('addFieldModal');
  const form = document.getElementById('field-form');
  if (fidx !== null && tables[idx][fidx]) {
    const field = tables[idx][fidx];
    form.field_name.value = field.name;
    form.field_type.value = field.type;
    if (form.field_options) {
      form.field_options.value = (field.options || []).join(', ');
    }
    if (form.foreign_key_target) {
      form.foreign_key_target.value = field.foreign_key || '';
    }
    form.field_type.dispatchEvent(new Event('change'));
    const btn = form.querySelector('button[type="submit"]');
    if (btn) btn.textContent = 'Save';
  } else {
    resetAddFieldForm();
  }
  modal.classList.remove('hidden');
  document.addEventListener('keydown', escHandler);
}

function hideAddFieldModal() {
  document.getElementById('addFieldModal').classList.add('hidden');
  document.removeEventListener('keydown', escHandler);
  if (addFieldTrigger) {
    addFieldTrigger.focus();
    addFieldTrigger = null;
  }
  editingFieldIdx = null;
  const form = document.getElementById('field-form');
  const btn = form.querySelector('button[type="submit"]');
  if (btn) btn.textContent = 'Add';
  resetAddFieldForm();
}

const escHandler = (e) => {
  if (e.key === 'Escape') hideAddFieldModal();
};

function resetAddFieldForm() {
  const form = document.getElementById('field-form');
  form.reset();
  const optionsContainer = document.getElementById('field-options-container');
  const fkContainer = document.getElementById('fk-select-container');
  if (optionsContainer) optionsContainer.classList.add('hidden');
  if (fkContainer) fkContainer.classList.add('hidden');
}

function addField(e) {
  e.preventDefault();
  const form = e.target;
  const name = form.field_name.value.trim();
  const type = form.field_type.value;
  if (!name || !type || type === 'Select type') return;

  const optionsText = form.field_options ? form.field_options.value.trim() : '';
  const options = optionsText
    ? optionsText.split(',').map((o) => o.trim()).filter((o) => o)
    : [];
  const fk = form.foreign_key_target ? form.foreign_key_target.value : '';

  if (editingFieldIdx !== null) {
    tables[currentTable][editingFieldIdx] = {
      name,
      type,
      options,
      foreign_key: fk,
    };
  } else {
    tables[currentTable].push({ name, type, options, foreign_key: fk });
  }
  updateFieldList(currentTable);
  hideAddFieldModal();
}

function removeField(tidx, fidx) {
  tables[tidx].splice(fidx, 1);
  updateFieldList(tidx);
}

function showTableSummaryModal() {
  const modal = document.getElementById('tableSummaryModal');
  const list = document.getElementById('table-summary-list');
  list.innerHTML = '';
  document.querySelectorAll('.table-form').forEach((div) => {
    const idx = parseInt(div.dataset.index, 10);
    const name = div.querySelector('input[name="table_name"]').value.trim();
    if (!name) return;
    const li = document.createElement('li');
    li.innerHTML = `<strong>${name}</strong>: ${
      (tables[idx] || [])
        .map((f) => f.name)
        .join(', ') || '(no fields)'
    }`;
    list.appendChild(li);
  });
  modal.classList.remove('hidden');
  document.addEventListener('keydown', summaryEscHandler);
}

function hideTableSummaryModal() {
  const modal = document.getElementById('tableSummaryModal');
  modal.classList.add('hidden');
  document.removeEventListener('keydown', summaryEscHandler);
}

const summaryEscHandler = (e) => {
  if (e.key === 'Escape') hideTableSummaryModal();
};

function updateFieldList(idx) {
  const list = document.getElementById(`fields-list_${idx}`);
  list.innerHTML = '';
  tables[idx].forEach((f, i) => {
    const li = document.createElement('li');
    li.className = 'flex justify-between items-center wizard-field-row';
    li.innerHTML = `<span>${f.name} (${f.type})</span>`;
    li.onclick = () => showAddFieldModal(idx, i);
    const btnGroup = document.createElement('div');
    btnGroup.className = 'space-x-2';

    const editBtn = document.createElement('button');
    editBtn.type = 'button';
    editBtn.textContent = 'Edit';
    editBtn.className = 'text-blue-600';
    editBtn.onclick = (e) => {
      e.stopPropagation();
      showAddFieldModal(idx, i);
    };
    btnGroup.appendChild(editBtn);

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.textContent = '×';
    removeBtn.className = 'text-red-600';
    removeBtn.onclick = (e) => {
      e.stopPropagation();
      removeField(idx, i);
    };
    btnGroup.appendChild(removeBtn);

    li.appendChild(btnGroup);
    list.appendChild(li);
  });
  document.getElementById(`fields_json_${idx}`).value = JSON.stringify(
    tables[idx]
  );
  updateTitleFieldOptions(idx);
}

function updateTitleFieldOptions(idx) {
  const select = document.getElementById(`title_field_select_${idx}`);
  if (!select) return;
  const prev = select.value;
  select.innerHTML = '<option value="" disabled>Select title field</option>';
  tables[idx].forEach((f) => {
    const opt = document.createElement('option');
    opt.value = f.name;
    opt.textContent = f.name;
    select.appendChild(opt);
  });
  if (tables[idx].length === 1) {
    select.value = tables[idx][0].name;
  } else if (tables[idx].some((f) => f.name === prev)) {
    select.value = prev;
  }
  select.disabled = tables[idx].length === 0;
}

let fieldTypes = null;

async function loadFieldTypes() {
  if (fieldTypes) return fieldTypes;
  try {
    const res = await fetch('/api/field-types');
    fieldTypes = await res.json();
  } catch {
    fieldTypes = {};
  }
  return fieldTypes;
}

async function initFieldTypeSelect() {
  const select = document.getElementById('field_type');
  if (!select) return;
  await loadFieldTypes();
  Object.keys(fieldTypes).forEach((t) => {
    const opt = document.createElement('option');
    opt.value = t;
    opt.textContent = t;
    select.appendChild(opt);
  });

  select.addEventListener('change', () => {
    const meta = fieldTypes[select.value] || {};
    const optionsContainer = document.getElementById('field-options-container');
    const fkContainer = document.getElementById('fk-select-container');
    if (optionsContainer) {
      optionsContainer.classList.toggle('hidden', !meta.allows_options);
    }
    if (fkContainer) {
      fkContainer.classList.toggle('hidden', !meta.allows_foreign_key);
    }
  });
}

function addTableForm() {
  const container = document.getElementById('tables-container');
  const idx = tables.length;
  tables.push([]);
  const div = document.createElement('div');
  div.className = 'table-form space-y-4 mb-6';
  div.dataset.index = idx;
  div.innerHTML = `
    <div class="form-group">
      <label class="block mb-1">Table Name</label>
      <input type="text" name="table_name" class="form-control w-full" />
    </div>
    <div class="form-group">
      <label class="block mb-1">Title Field</label>
      <select name="title_field" id="title_field_select_${idx}" class="form-control w-full" required>
        <option value="" disabled selected>Select title field</option>
      </select>
    </div>
    <div class="form-group">
      <label class="block mb-1">Description</label>
      <input type="text" name="description" class="form-control w-full" />
    </div>
    <input type="hidden" name="fields_json" id="fields_json_${idx}" />
    <div class="form-group">
      <h2 class="font-semibold mb-2">Fields</h2>
      <ul id="fields-list_${idx}" class="mb-2 list-disc pl-5"></ul>
      <button type="button" onclick="showAddFieldModal(${idx})" class="btn-secondary px-2 py-1 rounded">Add Field</button>
    </div>`;
  container.appendChild(div);
  updateTitleFieldOptions(idx);
  return idx;
}

window.showAddFieldModal = showAddFieldModal;
window.hideAddFieldModal = hideAddFieldModal;
window.addTableForm = addTableForm;
window.showTableSummaryModal = showTableSummaryModal;
window.hideTableSummaryModal = hideTableSummaryModal;

function initImportSchema() {
  const btn = document.getElementById('import-table-btn');
  const input = document.getElementById('import-table-file');
  if (!btn || !input) return;
  btn.addEventListener('click', () => input.click());
  input.addEventListener('change', handleImportFile);
}

function handleImportFile(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (evt) => {
    const text = evt.target.result;
    const lines = text.split(/\r?\n/).filter((l) => l.trim());
    if (lines.length === 0) return;
    const headers = lines[0]
      .split(',')
      .map((h) => h.replace(/^"|"$/g, '').trim())
      .filter((h) => h);
    let idx;
    if (
      tables.length === 1 &&
      tables[0].length === 0 &&
      !document
        .querySelector('.table-form[data-index="0"] input[name="table_name"]')
        .value.trim()
    ) {
      idx = 0;
    } else {
      idx = addTableForm();
    }
    const wrapper = document.querySelector(`.table-form[data-index="${idx}"]`);
    const nameInput = wrapper.querySelector('input[name="table_name"]');
    if (nameInput) {
      nameInput.value = file.name.replace(/\.csv$/i, '');
    }
    headers.forEach((h) => {
      tables[idx].push({ name: h, type: 'text', options: [], foreign_key: '' });
    });
    updateFieldList(idx);
    e.target.value = '';
  };
  reader.readAsText(file);
}

document.addEventListener('DOMContentLoaded', () => {
  initFieldTypeSelect();
  addTableForm();
  document.getElementById('field-form').addEventListener('submit', addField);
  initImportSchema();
  const summaryBtn = document.getElementById('schema-summary-btn');
  if (summaryBtn) summaryBtn.addEventListener('click', showTableSummaryModal);
});

window.initImportSchema = initImportSchema;
