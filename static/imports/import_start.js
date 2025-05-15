function compileRowsForImport() {
    // 1) Find all <select data-header> under #imported-fields-container
    const mapped = Array.from(
      document.querySelectorAll('#imported-fields-container select[data-header]')
    )
      // only those where the validation-results sibling contains a .matched-valid span
      .filter(sel => {
        const container = sel.closest('div[id^="match-container-"]');
        return container.querySelector('.matched-valid');
      })
      // map to { key: csvHeaderName, column: tableFieldName }
      .map(sel => ({
        key: sel.dataset.header,  // CSV header
        column: sel.value         // table field
      }));
  
    // 2) For each original row (window.importedRows), pick only those mapped columns
    return window.importedRows.map(row => {
      const out = {};
      mapped.forEach(({ key, column }) => {
        out[column] = row[key];
      });
      return out;
    });
  }

document.addEventListener('DOMContentLoaded', () => {
    const importBtn = document.getElementById('import-btn');
    const statusContainer = document.getElementById('import-status-container');
    const progressEl = document.getElementById('import-progress');
    const errorsEl = document.getElementById('import-errors');
    if (!importBtn || !statusContainer || !progressEl || !errorsEl) return;
  
    importBtn.addEventListener('click', event => {
      event.preventDefault();
      const table = importBtn.dataset.table;
      if (!table) return console.error('Import aborted: no table');
  
      const rows = compileRowsForImport();
      statusContainer.classList.remove('hidden');
      importBtn.disabled = true;
  
      fetch('/import-start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ table, rows })
      })
      .then(res => res.json())
      .then(({ importId, totalRows }) => {
        importBtn.dataset.importId = importId;
        progressEl.max = totalRows;
        let interval = setInterval(() => {
          fetch(`/import-status?importId=${importId}`)
            .then(r => r.json())
            .then(data => {
              progressEl.value = data.importedRows;
              if (data.errorCount > 0) {
                errorsEl.innerHTML = data.errors
                  .map(e => `Row ${e.row}: ${e.message}`)
                  .join('<br>');
              }
              if (data.status !== 'in_progress') {
                clearInterval(interval);
                const msg = data.status === 'complete'
                  ? '<div class="text-green-600">Import complete!</div>'
                  : '<div class="text-red-600">Import failed.</div>';
                errorsEl.insertAdjacentHTML('afterbegin', msg);
              }
            });
        }, 500);
      })
      .catch(err => console.error('Error starting import:', err));
    });
  });
  