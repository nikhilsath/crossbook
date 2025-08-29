// Handle form submission for JSON config items

function initLayoutDefaultsForms() {
  document.querySelectorAll('form[data-json-key="layout_defaults"]').forEach(form => {
    form.addEventListener('submit', e => {
      const width = {};
      form.querySelectorAll('input[name^="width."]').forEach(inp => {
        const key = inp.name.split('.')[1];
        width[key] = parseFloat(inp.value) || 0;
      });
      const height = {};
      form.querySelectorAll('input[name^="height."]').forEach(inp => {
        const key = inp.name.split('.')[1];
        height[key] = parseFloat(inp.value) || 0;
      });
      const hidden = form.querySelector('input[name="value"]');
      if (hidden) {
        hidden.value = JSON.stringify({ width, height });
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initLayoutDefaultsForms();
  // Handle title field selection radios
  document.querySelectorAll('input.title-radio').forEach(r => {
    r.addEventListener('change', async (e) => {
      const input = e.currentTarget;
      if (!input.checked) return;
      const table = input.dataset.table;
      const field = input.value;
      try {
        const resp = await fetch(`/admin/fields/${encodeURIComponent(table)}/title`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ field })
        });
        const data = await resp.json().catch(() => ({}));
        if (!resp.ok || !data.success) {
          alert('Failed to set title field');
        }
      } catch (err) {
        console.error('Title set failed', err);
        alert('Failed to set title field');
      }
    });
  });
  // Handle readonly checkbox toggles
  document.querySelectorAll('input.readonly-checkbox').forEach(cb => {
    cb.addEventListener('change', async (e) => {
      const el = e.currentTarget;
      const table = el.dataset.table;
      const field = el.dataset.field;
      const want = el.checked ? 1 : 0;
      try {
        const resp = await fetch(`/admin/fields/${encodeURIComponent(table)}/readonly`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ field, readonly: want })
        });
        const data = await resp.json().catch(() => ({}));
        if (!resp.ok || !data.success) throw new Error(data.error || 'update_failed');
      } catch (err) {
        console.error('[fields_admin] readonly update failed', err);
        // revert UI
        el.checked = !el.checked;
        alert('Failed to update read-only flag');
      }
    });
  });
  // Change type popover handlers
  (function initChangeTypePopovers(){
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

    function closeAllPopovers(except) {
      document.querySelectorAll('[data-popover]').forEach(p => {
        if (p !== except) p.classList.add('hidden');
      });
    }

    document.addEventListener('click', (e) => {
      const btn = e.target.closest('.btn-change');
      if (btn) {
        const cell = btn.closest('td');
        const pop = cell?.querySelector('[data-popover]');
        if (!pop) return;
        e.stopPropagation();
        const select = pop.querySelector('.field-type-select');
        // Populate once
        (async () => {
          const types = await loadFieldTypes();
          if (select && select.options.length === 0) {
            Object.keys(types).forEach(t => {
              const opt = document.createElement('option');
              opt.value = t;
              opt.textContent = t;
              select.appendChild(opt);
            });
            const cur = select.dataset.currentType;
            if (cur && types[cur]) select.value = cur;
          }
        })();
        // Toggle popover
        const isHidden = pop.classList.contains('hidden');
        closeAllPopovers(isHidden ? pop : null);
        pop.classList.toggle('hidden');
        return;
      }
      // click outside -> close
      if (!e.target.closest('[data-popover]')) closeAllPopovers();
    });

    // When a type is selected, run a handler that logs inputs
    async function handleFieldTypeSelected(table, field, newType, selectEl) {
      console.info('[fields_admin] handleFieldTypeSelected', { table, field, newType });
      const popover = selectEl?.closest('[data-popover]');
      const msgEl = popover?.querySelector('[data-validation-msg]');
      if (msgEl) {
        msgEl.classList.add('hidden');
        msgEl.textContent = '';
      }

      try {
        const resp = await fetch('/admin/fields/validate-type', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ table, field, new_type: newType })
        });
        const report = await resp.json();
        if (!resp.ok || !report || typeof report !== 'object') {
          throw new Error('bad_response');
        }
        const invalid = Number(report.invalid || 0);
        if (invalid > 0 && msgEl) {
          msgEl.textContent = `${invalid} row(s) incompatible with ${newType}. Clear values first.`;
          msgEl.classList.remove('hidden');
          // Hide convert button if present
          const btn = popover.querySelector('[data-convert]');
          if (btn) btn.classList.add('hidden');
          return;
        }

        // No invalid rows: show Convert button
        let btn = popover.querySelector('[data-convert]');
        if (!btn) {
          btn = document.createElement('button');
          btn.type = 'button';
          btn.dataset.convert = '1';
          btn.className = 'btn-secondary mt-2 px-3 py-1 rounded';
          btn.textContent = 'Convert';
          popover.appendChild(btn);
          btn.addEventListener('click', async () => {
            try {
              const r = await fetch('/admin/fields/convert-type', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ table, field, new_type: newType })
              });
              const payload = await r.json().catch(() => ({}));
              if (!r.ok || !payload.success) throw new Error(payload.error || 'convert_failed');

              // Update UI: type cell text and toggle title radio visibility
              const row = selectEl.closest('tr');
              const typeCell = row?.querySelector('td:nth-child(3)');
              if (typeCell) typeCell.textContent = newType;
              const titleCell = row?.querySelector('td:nth-child(1)');
              const radio = titleCell?.querySelector('input.title-radio');
              if (radio) {
                const allowed = new Set(['text','date','url','select','number']);
                radio.classList.toggle('hidden', !allowed.has(newType));
              }
              // Close popover
              popover.classList.add('hidden');
            } catch (err) {
              console.error('[fields_admin] convert failed', err);
              if (msgEl) {
                msgEl.textContent = 'Conversion failed — see logs';
                msgEl.classList.remove('hidden');
              }
            }
          });
        }
        btn.classList.remove('hidden');
      } catch (err) {
        console.error('[fields_admin] server validation failed', err);
        if (msgEl) {
          msgEl.textContent = 'Validation failed — see logs';
          msgEl.classList.remove('hidden');
        }
      }
    }

    document.addEventListener('change', (e) => {
      const sel = e.target.closest('.field-type-select');
      if (!sel) return;
      const table = sel.dataset.table;
      const field = sel.dataset.field;
      const newType = sel.value;
      handleFieldTypeSelected(table, field, newType, sel);
    });
  })();

  // Clear values handler with confirmation
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.clear-btn');
    if (!btn) return;
    const table = btn.dataset.table;
    const field = btn.dataset.field;
    // Query current count for confirmation context
    let count = 0;
    try {
      const resp = await fetch(`/${encodeURIComponent(table)}/count-nonnull?field=${encodeURIComponent(field)}`);
      const data = await resp.json();
      count = Number(data.count || 0);
    } catch {}
    const sure = window.confirm(`Are you sure you want to clear ${count} value(s) from ${table}.${field}?`);
    if (!sure) return;
    try {
      const resp = await fetch(`/admin/fields/${encodeURIComponent(table)}/clear`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ field })
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok || !data.success) throw new Error(data.error || 'clear_failed');
      // Update the Not Null count cell to 0
      const row = btn.closest('tr');
      const nnCell = row?.querySelector('td:nth-child(4)');
      if (nnCell) nnCell.textContent = '0';
    } catch (err) {
      console.error('[fields_admin] clear failed', err);
      alert('Failed to clear values — see logs');
    }
  });
});
