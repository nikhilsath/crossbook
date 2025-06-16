let bulkTrigger = null;
let escHandler = (e) => {
  if (e.key === 'Escape') {
    closeBulkEditModal();
  }
};

export function openBulkEditModal() {
  updateSelectedCount();
  bulkTrigger = document.activeElement;
  document.getElementById('bulkEditModal').classList.remove('hidden');
  document.addEventListener('keydown', escHandler);
}

export function closeBulkEditModal() {
  document.getElementById('bulkEditModal').classList.add('hidden');
  document.removeEventListener('keydown', escHandler);
  if (bulkTrigger) {
    bulkTrigger.focus();
    bulkTrigger = null;
  }
}

let tableName;
let bulkBtn;
let exportBtn;

function updateSelectedCount() {
  const count = document.querySelectorAll('.row-select:checked').length;
  const el = document.getElementById('bulk-edit-count');
  if (el) {
    el.textContent = `${count} record${count === 1 ? '' : 's'} selected`;
  }
}

function updateBulkButtonState() {
  const any = document.querySelectorAll('.row-select:checked').length > 0;
  if (bulkBtn) {
    bulkBtn.disabled = !any;
    bulkBtn.classList.toggle('opacity-50', !any);
  }
  if (exportBtn) {
    exportBtn.disabled = !any;
    exportBtn.classList.toggle('opacity-50', !any);
  }
  updateSelectedCount();
}

function buildInput() {
  const sel = document.getElementById('bulk-field');
  const optEl = sel.selectedOptions[0];
  const type = optEl.dataset.type;
  const options = optEl.dataset.options ? JSON.parse(optEl.dataset.options) : [];
  const container = document.getElementById('bulk-input-container');
  let html = '';
  if (type === 'textarea') {
    html = '<textarea id="bulk-value" class="w-full border px-2 py-1 rounded"></textarea>';
  } else if (type === 'number') {
    html = '<input id="bulk-value" type="number" class="w-full border px-2 py-1 rounded">';
  } else if (type === 'boolean') {
    html = '<select id="bulk-value" class="w-full border px-2 py-1 rounded"><option value="1">True</option><option value="0">False</option></select>';
  } else if (type === 'select') {
    html = '<select id="bulk-value" class="w-full border px-2 py-1 rounded">' +
      options.map(o => `<option value="${o}">${o}</option>`).join('') +
      '</select>';
  } else if (type === 'multi_select' || type === 'foreign_key') {
    html = '<div class="max-h-48 overflow-y-auto border p-2 space-y-1">' +
      options.map(o => `<label class="flex items-center space-x-2"><input type="checkbox" value="${o}" class="bulk-multi-option"><span class="text-sm">${o}</span></label>`).join('') +
      '</div>';
  } else if (type === 'url') {
    html = '<input id="bulk-value" type="url" class="w-full border px-2 py-1 rounded">';
  } else {
    html = '<input id="bulk-value" type="text" class="w-full border px-2 py-1 rounded">';
  }
  container.innerHTML = html;
}

function exportSelected() {
  const ids = Array.from(document.querySelectorAll('.row-select:checked')).map(cb => cb.value);
  if (ids.length === 0) return;
  const params = new URLSearchParams();
  params.set('ids', ids.join(','));
  window.location = `/${tableName}/export?` + params.toString();
}

document.addEventListener('DOMContentLoaded', () => {
  tableName = document.getElementById('records-table').dataset.table;
  bulkBtn = document.getElementById('bulk_edit');
  exportBtn = document.getElementById('export_csv');
  buildInput();
  document.getElementById('bulk-field').addEventListener('change', buildInput);

  document.querySelectorAll('.row-select').forEach(cb => {
    cb.addEventListener('change', updateBulkButtonState);
  });
  const selectAll = document.getElementById('select-all-rows');
  if (selectAll) {
    selectAll.addEventListener('change', () => {
      const checked = selectAll.checked;
      document.querySelectorAll('.row-select').forEach(cb => {
        cb.checked = checked;
      });
      updateBulkButtonState();
    });
  }
  updateBulkButtonState();

  if (exportBtn) {
    exportBtn.addEventListener('click', exportSelected);
  }

  document.getElementById('bulk-edit-form').addEventListener('submit', e => {
    e.preventDefault();
    const ids = Array.from(document.querySelectorAll('.row-select:checked')).map(cb => cb.value);
    const fieldSel = document.getElementById('bulk-field');
    const field = fieldSel.value;
    const type = fieldSel.selectedOptions[0].dataset.type;
    let value;
    if (type === 'multi_select' || type === 'foreign_key') {
      value = Array.from(document.querySelectorAll('.bulk-multi-option:checked')).map(cb => cb.value);
    } else {
      value = document.getElementById('bulk-value').value;
    }
    fetch(`/${tableName}/bulk-update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
      body: JSON.stringify({ ids, field, value })
    })
      .then(resp => {
        if (!resp.ok) throw new Error('error');
        return resp.json();
      })
      .then(() => {
        const status = document.getElementById('bulk-edit-status');
        status.textContent = 'Updated!';
        status.classList.remove('hidden', 'text-red-600');
        status.classList.add('text-green-600');
        setTimeout(() => location.reload(), 500);
      })
      .catch(() => {
        const status = document.getElementById('bulk-edit-status');
        status.textContent = 'Error updating records';
        status.classList.remove('hidden', 'text-green-600');
        status.classList.add('text-red-600');
      });
  });
});

window.openBulkEditModal = openBulkEditModal;
window.closeBulkEditModal = closeBulkEditModal;
window.exportSelected = exportSelected;
