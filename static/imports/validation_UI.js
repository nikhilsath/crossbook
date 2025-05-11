// static/imports/validation_UI.js

// Show the validation modal in the centered overlay
function showValidationPopup(header, htmlContent) {
    const overlay = document.getElementById('validationOverlay');
    const popup   = document.getElementById('validation-popup');
    if (!popup || !overlay) return;
  
    popup.innerHTML = `<strong>${header}:</strong> ${htmlContent}`;
    overlay.classList.remove('hidden');
  }
  
  // Wait until the DOM is loaded
  document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('imported-fields-container');
    if (!container) return;
  
    // Delegate clicks to blank-popup spans only
    container.addEventListener('click', event => {
      const span = event.target.closest('span.blank-popup');
      if (!span) return;
  
      const header    = span.dataset.popupKey;
      const blankRows = window.validationReport?.[header]?.details?.blank || [];
  
      const content = blankRows.length
        ? `<p><strong>Blank rows:</strong> ${blankRows.join(', ')}</p>`
        : `<p>No blanks detected.</p>`;
  
      showValidationPopup(header, content);
    });
  
    // Delegate clicks to warning-popup spans only
    container.addEventListener('click', event => {
      const span = event.target.closest('span.warning-popup');
      if (!span) return;
  
      const header   = span.dataset.popupKey;
      const warnings = window.validationReport?.[header]?.details?.warning || [];
  
      let content;
      if (warnings.length) {
        const items = warnings
          .map(w => `<li>Row ${w.row}${w.message ? `: ${w.message}` : ''}${w.reason ? ` (${w.reason})` : ''}</li>`)
          .join('');
        content = `<p><strong>Warnings:</strong></p><ul>${items}</ul>`;
      } else {
        content = `<p>No warnings detected.</p>`;
      }
  
      showValidationPopup(header, content);
    });
  
    // Delegate clicks to valid-popup spans only
    container.addEventListener('click', event => {
      const span = event.target.closest('span.valid-popup');
      if (!span) return;
  
      const header    = span.dataset.popupKey;
      const validRows = window.validationReport?.[header]?.details?.valid || [];
  
      const content = validRows.length
        ? `<p><strong>Valid rows:</strong> ${validRows.join(', ')}</p>`
        : `<p>No valid rows detected.</p>`;
  
      showValidationPopup(header, content);
    });
  
    // Delegate clicks to invalid-popup spans only
    container.addEventListener('click', event => {
      const span = event.target.closest('span.invalid-popup[data-popup-key]');
      if (!span) return;
  
      const header      = span.dataset.popupKey;
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
  
      showValidationPopup(header, content);
    });
  });
  
  // Hide the modal when clicking outside of any result span or the popup itself
  document.addEventListener('click', event => {
    const overlay = document.getElementById('validationOverlay');
    const popup   = document.getElementById('validation-popup');
    if (!popup || !overlay) return;
  
    const isResult = !!event.target.closest('span[data-popup-key]');
    if (!isResult && !popup.contains(event.target)) {
      overlay.classList.add('hidden');
    }
  });
  
  function updateImportButtonState() {
    const invalidCount = document.querySelectorAll(
      '#available-fields-list .matched-invalid'
    ).length;
    const validCount = document.querySelectorAll(
      '#available-fields-list .matched-valid'
    ).length;
    const btn = document.getElementById('import-btn');
  
    if (invalidCount === 0 && validCount > 0) {
      btn.removeAttribute('disabled');
      btn.classList.remove('opacity-50', 'cursor-not-allowed');
    } else {
      btn.setAttribute('disabled', '');
      btn.classList.add('opacity-50', 'cursor-not-allowed');
    }
  }
  document.addEventListener('DOMContentLoaded', updateImportButtonState);
  updateImportButtonState();