document.addEventListener('DOMContentLoaded', () => {
  const importBtn        = document.getElementById('import-btn');
  const statusContainer  = document.getElementById('import-status-container');
  const progressEl       = document.getElementById('import-progress');
  const errorsEl         = document.getElementById('import-errors');

  if (!importBtn || !statusContainer || !progressEl || !errorsEl) {
    console.error('Progress bar elements missing from the page');
    return;
  }

  importBtn.addEventListener('click', () => {
    importBtn.disabled = true;
    statusContainer.classList.remove('hidden');

    const fileInput = document.querySelector('input[type="file"]');
    const payload = {
      table: importBtn.dataset.table,
      rows: window.importedRows || []
    };

    if (fileInput && fileInput.files.length > 0) {
      // Fallback for old workflow using uploaded CSVs
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      formData.append('table', payload.table);
      fetch('/import-start', {
        method: 'POST',
        body: formData
      })
      .then(res => res.json())
      .then(handleResponse);
      return;
    }

    fetch('/import-start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(handleResponse);

    function handleResponse({ importId, totalRows }) {
      progressEl.max = totalRows;
      const interval = setInterval(() => {
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
    }
  });
});
