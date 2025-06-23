// Global match tracker
const matchedFields = {};

// Update matched display inline card
function updateMatchedDisplay(headerName, field) {
  const wrapper = document.getElementById(`select-wrapper-${headerName}`);
  if (!wrapper) return;

  wrapper.innerHTML = `
    <span class="inline-block bg-green-100 text-green-800 text-sm px-3 py-1 rounded">
      Matched to: <strong>${field}</strong>
      <button onclick="unmatchField('${headerName}')" class="ml-2 text-red-600">✕</button>
    </span>
  `;
}

// Remove a match
function unmatchField(headerName) {
  delete matchedFields[headerName];
  const wrapper = document.getElementById(`select-wrapper-${headerName}`);
  if (!wrapper) return;
  wrapper.innerHTML = generateDropdownHTML(headerName);
  refreshDropdowns();
  renderAvailableFields();
}

// Hide already matched fields in other dropdowns
function refreshDropdowns() {
  const selects = document.querySelectorAll("select[data-header]");
  selects.forEach(select => {
    const currentHeader = select.getAttribute("data-header");
    const currentValue = matchedFields[currentHeader]?.field || "";

    Array.from(select.options).forEach(option => {
      if (option.value === "") return; // skip the unmatch/placeholder option
      const isMatched = Object.values(matchedFields).some(
        mf => mf.field === option.value
      );
      const isCurrent = option.value === currentValue;
      option.hidden = isMatched && !isCurrent;
    });
  });
}

// Generate the dropdown HTML from a template
function generateDropdownHTML(headerName) {
  const options = document
    .querySelector('#dropdown-template')
    ?.innerHTML
    ?.replace(/__HEADER__/g, headerName) || "";
  return options;
}

// On load, hide matched options in initial dropdowns
document.addEventListener("DOMContentLoaded", () => {
  refreshDropdowns();
  renderAvailableFields();
});

// Render the list of available fields on the right
function renderAvailableFields() {
  const container = document.getElementById("available-fields-list");
  if (!container) return;
  container.innerHTML = Object.entries(fieldSchema)
    .map(([field, meta]) => {
      const matched = Object.values(matchedFields).some(
        mf => mf.field === field
      );
      return `
        <div class="border px-3 py-2 available-field-${field} rounded bg-gray-50">
          <strong>${field}</strong> — ${meta.type} — matched: ${matched}
        </div>
      `;
    })
    .join("");
} 


// Delegate change events to all dropdowns for matching and validation
document.addEventListener("change", event => {
    if (!event.target.matches("select[data-header][data-table]")) return;
    const header = event.target.dataset.header;
    const table = event.target.dataset.table;
    const selectedField = event.target.value;
    if (!selectedField) return;
  
    // Map header to its table & field
    matchedFields[header] = { table, field: selectedField };
    updateMatchedDisplay(header, selectedField);
  
    // Send full mapping + CSV rows to server for validation
    fetch("/trigger-validation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ matchedFields, rows: window.importedRows })
    })
      .then(res => {
        if (!res.ok) throw new Error(`Validation failed: ${res.status}`);
        return res.json();
      })
      .then(report => {
        // Store the full validation report for popups
        window.validationReport = report;
  
        // Render validation results inline
        Object.entries(report).forEach(([respHeader, results]) => {
          const container = document.getElementById(`match-container-${respHeader}`);
          if (!container) return;
  
          // Remove previous results
          const oldResults = container.querySelector('.validation-results');
          if (oldResults) oldResults.remove();
  
          // Create new block
          const block = document.createElement('div');
          block.className = 'text-xs ml-4 space-x-2 validation-results';
          block.innerHTML =
            `<span data-popup-key="${respHeader}" class="text-green-600 valid-popup">✅ ${results.valid} valid</span>` +
            `<span data-popup-key="${respHeader}" class="text-yellow-600 warning-popup">⚠️ ${results.warning ?? 0} warnings</span>` +
            `<span data-popup-key="${respHeader}" class="text-red-600 invalid-popup">❌ ${results.invalid} invalid</span>` +
            `<span data-popup-key="${respHeader}" class="blank-popup">⬛ ${results.blank} blank</span>`;
  
          // Insert into DOM, placing before select-wrapper if present
          const flexRow = container.querySelector('.flex.justify-between');
          const selectWrapper = flexRow?.querySelector(`#select-wrapper-${respHeader}`);
          if (flexRow && selectWrapper) {
            flexRow.insertBefore(block, selectWrapper);
          } else {
            container.appendChild(block);
          }
        });
  
        // After rendering validation, update UI and dropdowns
        renderAvailableFields();
        refreshDropdowns();
        console.log('Full report:', report);  
        Object.entries(report).forEach(([respHeader, results]) => {
          const container = document.getElementById(`match-container-${respHeader}`);
          if (!container) return;
        });
        renderAvailableFields();
        refreshDropdowns();
        Object.entries(report).forEach(([header, entry]) => {
          const cssClass = entry.cssClass;
          if (!cssClass) return; 
  
          // Lookup what table-field this CSV header was matched to
          const match      = matchedFields[header];
          const fieldName  = match?.field;                  // e.g. "chapter", "source"
          if (!fieldName) return;                          // no dropdown choice yet
    
          // Select that card by the class your renderAvailableFields adds:
          // <div class="… available-field-<fieldName> …">
          const card = document.querySelector(`.available-field-${fieldName}`);
          if (card) {
            cssClass.split(/\s+/).forEach(cls => {
              if (cls) card.classList.add(cls);
            });            
          }
        });
        updateImportButtonState();
      })
      .catch(err => console.error(err));
    });