let tables = [];
let currentTable = 0;
let addFieldTrigger = null;

function showAddFieldModal(idx) {
  currentTable = idx;
  addFieldTrigger = document.activeElement;
  document.getElementById('addFieldModal').classList.remove('hidden');
  document.addEventListener('keydown', escHandler);
}

function hideAddFieldModal() {
  document.getElementById('addFieldModal').classList.add('hidden');
  document.removeEventListener('keydown', escHandler);
  if (addFieldTrigger) {
    addFieldTrigger.focus();
    addFieldTrigger = null;
  }
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

  tables[currentTable].push({ name, type, options, foreign_key: fk });
  updateFieldList(currentTable);
  hideAddFieldModal();
  resetAddFieldForm();
}

function removeField(tidx, fidx) {
  tables[tidx].splice(fidx, 1);
  updateFieldList(tidx);
}

function updateFieldList(idx) {
  const list = document.getElementById(`fields-list_${idx}`);
  list.innerHTML = '';
  tables[idx].forEach((f, i) => {
    const li = document.createElement('li');
    li.className = 'flex justify-between items-center';
    li.innerHTML = `<span>${f.name} (${f.type})</span>`;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = '×';
    btn.className = 'text-red-600 ml-2';
    btn.onclick = () => removeField(idx, i);
    li.appendChild(btn);
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

function initFieldTypeSelect() {
  const select = document.getElementById('field_type');
  if (!select) return;
  fetch('/api/field-types')
    .then((res) => res.json())
    .then((types) => {
      types.forEach((t) => {
        if (t === 'title') return;
        const opt = document.createElement('option');
        opt.value = t;
        opt.textContent = t;
        select.appendChild(opt);
      });
    })
    .catch(() => {});

  select.addEventListener('change', () => {
    const type = select.value;
    const optionsContainer = document.getElementById('field-options-container');
    const fkContainer = document.getElementById('fk-select-container');
    if (optionsContainer) {
      if (type === 'select' || type === 'multi_select') {
        optionsContainer.classList.remove('hidden');
      } else {
        optionsContainer.classList.add('hidden');
      }
    }
    if (fkContainer) {
      if (type === 'foreign_key') {
        fkContainer.classList.remove('hidden');
      } else {
        fkContainer.classList.add('hidden');
      }
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
}

document.addEventListener('DOMContentLoaded', () => {
  initFieldTypeSelect();
  addTableForm();
  document.getElementById('field-form').addEventListener('submit', addField);
});

window.showAddFieldModal = showAddFieldModal;
window.hideAddFieldModal = hideAddFieldModal;
window.addTableForm = addTableForm;
