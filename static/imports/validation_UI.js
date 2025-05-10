
function showValidationPopup(header, htmlContent, x, y) {
    const popup = document.getElementById('validation-popup');
    if (!popup) return;
    popup.innerHTML = `<strong>${header}:</strong> ${htmlContent}`;
    popup.style.top  = `${y + 8}px`;
    popup.style.left = `${x + 8}px`;
    popup.classList.remove('hidden');
  }
  
  // Wait until the DOM is loaded
  document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('imported-fields-container');
    if (!container) return;
  
    // Delegate clicks to blank-popup spans only
    container.addEventListener('click', event => {
      const span = event.target.closest('span.blank-popup');
      if (!span) return;
  
      const header = span.dataset.popupKey;
      const blankRows = window.validationReport?.[header]?.details?.blank || [];
  
      const content = blankRows.length
        ? `<p><strong>Blank rows:</strong> ${blankRows.join(', ')}</p>`
        : `<p>No blanks detected.</p>`;
  
      showValidationPopup(header, content, event.pageX, event.pageY);
    });
     // Delegate clicks to warning-popup spans only
  container.addEventListener('click', event => {
    const span = event.target.closest('span.warning-popup');
    if (!span) return;

    const header = span.dataset.popupKey;
    const warnings = window.validationReport?.[header]?.details?.warning || [];

    let content;
    if (warnings.length) {
      // If warnings are objects with message/details
      const items = warnings
        .map(w => `<li>Row ${w.row}${w.message ? `: ${w.message}` : ''}${w.reason ? ` (${w.reason})` : ''}</li>`)
        .join('');
      content = `<p><strong>Warnings:</strong></p><ul>${items}</ul>`;
    } else {
      content = `<p>No warnings detected.</p>`;
    }

    showValidationPopup(header, content, event.pageX, event.pageY);
  });
    // Delegate clicks to valid-popup spans only
  container.addEventListener('click', event => {
    const span = event.target.closest('span.valid-popup');
    if (!span) return;

    const header = span.dataset.popupKey;
    const validRows = window.validationReport?.[header]?.details?.valid || [];

    const content = validRows.length
      ? `<p><strong>Valid rows:</strong> ${validRows.join(', ')}</p>`
      : `<p>No valid rows detected.</p>`;

    showValidationPopup(header, content, event.pageX, event.pageY);
  });
    // Delegate clicks to invalid-popup spans only
  container.addEventListener('click', event => {
    const span = event.target.closest('span.invalid-popup[data-popup-key]');
    if (!span) return;

    const header = span.dataset.popupKey;
    const invalidRows = window.validationReport?.[header]?.details?.invalid || [];

    let content;
    if (invalidRows.length) {
      const items = invalidRows
        .map(w => 
          typeof w === 'object'
            ? `<li>Row ${w.row}: ${w.reason}${w.value ? ` (value: ${w.value})` : ''}</li>`
            : `<li>Row ${w}</li>`
        )
        .join('');
      content = `<p><strong>Invalid rows:</strong></p><ul>${items}</ul>`;
    } else {
      content = `<p>No invalid rows detected.</p>`;
    }
    showValidationPopup(header, content, event.pageX, event.pageY);
  });
  });
  
  // Hide the popup when clicking outside of a result span or the popup itself
  document.addEventListener('click', event => {
    const popup = document.getElementById('validation-popup');
    if (!popup) return;
    const isResult = !!event.target.closest('span[data-popup-key]');
    if (!isResult && !popup.contains(event.target)) {
      popup.classList.add('hidden');
    }
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
  