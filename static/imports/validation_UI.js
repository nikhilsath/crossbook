function showValidationPopup(header, text, x, y) {
    const popup = document.getElementById('validation-popup');
    if (!popup) return;
    popup.textContent = `${header}: ${text}`;
    popup.style.top = `${y + 8}px`;
    popup.style.left = `${x + 8}px`;
    popup.classList.remove('hidden');
  }
  
  document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('imported-fields-container');
    if (!container) return;
  
    container.addEventListener('click', event => {
      const span = event.target.closest('.validation-results span');
      if (!span) return;
      const header = span.closest('[id^="match-container-"]')?.id.replace('match-container-', '');
      const text = span.textContent.trim();
      if (header && text) {
        showValidationPopup(header, text, event.pageX, event.pageY);
      }
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
  