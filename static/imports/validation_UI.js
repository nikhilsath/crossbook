
function showValidationPopup(header, htmlContent, x, y) {
    const popup = document.getElementById('validation-popup');
    if (!popup) return;
    popup.innerHTML = `<strong>${header}:</strong> ${htmlContent}`;
    popup.style.top = `${y + 8}px`;
    popup.style.left = `${x + 8}px`;
    popup.classList.remove('hidden');
  }
  
  document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('imported-fields-container');
    container.addEventListener('click', event => {
      const span   = event.target.closest('span[data-popup-key]');
      if (!span) return;
      const header = span.dataset.popupKey;
      const rows   = window.importedRows || [];
  
      // Find all row indices where this header is blank
      const blankRows = rows
        .map((row, idx) => ({ value: row[header], rowNum: idx + 1 }))
        .filter(({ value }) => value == null || String(value).trim() === '')
        .map(({ rowNum }) => rowNum);
  
      // Build popup HTML
      let content;
      if (blankRows.length) {
        content = `<p><strong>Blank rows:</strong> ${blankRows.join(', ')}</p>`;
      } else {
        content = '<p>No blanks detected.</p>';
      }
  
      // Show popup
      showValidationPopup(header, content, event.pageX, event.pageY);
    });
  });
  
  
  // Hide the popup when clicking outside of a result span or the popup itself
  document.addEventListener('click', event => {
    const popup = document.getElementById('validation-popup');
    if (!popup) return;
    const isResult = !!event.target.closest('.validation-results span');
    if (!isResult && !popup.contains(event.target)) {
      popup.classList.add('hidden');
    }
  });
  