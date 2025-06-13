let fields = [];

function showAddFieldModal() {
  document.getElementById('addFieldModal').classList.remove('hidden');
}

function hideAddFieldModal() {
  document.getElementById('addFieldModal').classList.add('hidden');
}

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
  const options = optionsText ? optionsText.split(',').map(o => o.trim()).filter(o => o) : [];
  const fk = form.foreign_key_target ? form.foreign_key_target.value : '';

  fields.push({name, type, options, foreign_key: fk});
  updateFieldList();
  hideAddFieldModal();
  resetAddFieldForm();
}

function removeField(index) {
  fields.splice(index, 1);
  updateFieldList();
}

function updateFieldList() {
  const list = document.getElementById('fields-list');
  list.innerHTML = '';
  fields.forEach((f, idx) => {
    const li = document.createElement('li');
    li.className = 'flex justify-between items-center';
    li.innerHTML = `<span>${f.name} (${f.type})</span>`;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = '×';
    btn.className = 'text-red-600 ml-2';
    btn.onclick = () => removeField(idx);
    li.appendChild(btn);
    list.appendChild(li);
  });
  document.getElementById('fields_json').value = JSON.stringify(fields);
}

document.addEventListener('DOMContentLoaded', () => {
  const select = document.getElementById('field_type');
  if (select) {
    fetch('/api/field-types')
      .then(res => res.json())
      .then(types => {
        types.forEach(t => {
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

  document.getElementById('field-form').addEventListener('submit', addField);
});

window.showAddFieldModal = showAddFieldModal;
window.hideAddFieldModal = hideAddFieldModal;
