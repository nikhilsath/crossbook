
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
      const span = event.target.closest('span.blank-popup[data-popup-key]');
      if (!span) return;
  
      const header = span.dataset.popupKey;
      const blankRows = window.validationReport?.[header]?.details?.blank || [];
  
      const content = blankRows.length
        ? `<p><strong>Blank rows:</strong> ${blankRows.join(', ')}</p>`
        : `<p>No blanks detected.</p>`;
  
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
  