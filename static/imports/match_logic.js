// Global match tracker
const matchedFields = {};

function handleDropdownChange(event, headerName) {
  const selectedField = event.target.value;
  if (!selectedField) return;

  matchedFields[headerName] = selectedField;
  const table = event.target.dataset.table;
  const fieldType = fieldSchema[selectedField]?.type || "unknown";
  validation_sorter(table, selectedField, headerName, fieldType);
  updateMatchedDisplay(headerName, selectedField);
  refreshDropdowns();
  renderAvailableFields();
  fetch('/trigger-validation', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ field: headerName })  
  });
}

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

function unmatchField(headerName) {
  delete matchedFields[headerName];
  const wrapper = document.getElementById(`select-wrapper-${headerName}`);
  if (!wrapper) return;
  wrapper.innerHTML = generateDropdownHTML(headerName);
  refreshDropdowns();
}

function refreshDropdowns() {
  const selects = document.querySelectorAll("select[data-header]");
  selects.forEach(select => {
    const currentHeader = select.getAttribute("data-header");
    const currentValue = matchedFields[currentHeader] || "";

    Array.from(select.options).forEach(option => {
      if (option.value === "") return; // skip unmatch option
      const isMatched = Object.values(matchedFields).includes(option.value);
      const isCurrent = option.value === currentValue;
      option.hidden = isMatched && !isCurrent;
    });
  });
}

function generateDropdownHTML(headerName) {
  const options = document
    .querySelector(`#dropdown-template`)?.innerHTML
    ?.replace(/__HEADER__/g, headerName) || "";
  return options;
}

document.addEventListener("DOMContentLoaded", () => {
  refreshDropdowns();
});

function renderAvailableFields() {
    const container = document.getElementById("available-fields-list");
    if (!container) return;
  
    container.innerHTML = Object.entries(fieldSchema).map(([field, meta]) => {
      const matched = Object.values(matchedFields).includes(field);
      return `
        <div class="border px-3 py-2 rounded bg-gray-50">
          <strong>${field}</strong> — ${meta.type} — matched: ${matched}
        </div>
      `;
    }).join("");
  }
  
  document.querySelectorAll('select[data-header][data-table]').forEach(select => {
    select.addEventListener('change', event => {
      const header = event.target.dataset.header;
      const table = event.target.dataset.table;
      const field = event.target.value;
  
      if (!field) return;
  
      matchedFields[header] = field;
      updateMatchedDisplay(header, field);
      refreshDropdowns();
      renderAvailableFields();
  
      const fieldType = fieldSchema[field]?.type || "unknown";
      fetch("/trigger-validation", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ table, field, header }),
      })
      .then(res => res.json())
      .then(data => {
        console.log("Server validation response:", data);
      });      
    });
  });
  