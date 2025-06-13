document.addEventListener("DOMContentLoaded", () => {
    const fieldTypeSelect = document.getElementById("field_type");
    const optionsContainer = document.getElementById("field-options-container");
    const fkSelectContainer = document.getElementById("fk-select-container");

    if (!fieldTypeSelect) return;

    fetch('/api/field-types')
      .then(res => res.json())
      .then(types => {
        types.forEach(t => {
          const opt = document.createElement('option');
          opt.value = t;
          opt.textContent = t;
          fieldTypeSelect.appendChild(opt);
        });
      })
      .catch(() => {});

    fieldTypeSelect.addEventListener("change", () => {
      const type = fieldTypeSelect.value;
  
      if (optionsContainer) {
        if (type === "select" || type === "multi_select") {
          optionsContainer.classList.remove("hidden");
        } else {
          optionsContainer.classList.add("hidden");
        }
      }
  
      if (fkSelectContainer) {
        if (type === "foreign_key") {
          fkSelectContainer.classList.remove("hidden");
        } else {
          fkSelectContainer.classList.add("hidden");
        }
      }
    });
  });
  

// Initialize Add/Remove tabs
function initEditFieldsTabs() {
  const tabAdd = document.getElementById("tab-add");
  const tabRemove = document.getElementById("tab-remove");
  const paneAdd = document.getElementById("pane-add");
  const paneRemove = document.getElementById("pane-remove");

  tabAdd.addEventListener("click", () => {
    tabAdd.classList.add("border-blue-600", "text-blue-600");
    tabRemove.classList.remove("border-blue-600", "text-blue-600");
    paneAdd.classList.remove("hidden");
    paneRemove.classList.add("hidden");
  });

  tabRemove.addEventListener("click", () => {
    tabRemove.classList.add("border-blue-600", "text-blue-600");
    tabAdd.classList.remove("border-blue-600", "text-blue-600");
    paneRemove.classList.remove("hidden");
    paneAdd.classList.add("hidden");
  });
}

// Store fetched counts here
let removeCounts = {};
function fetchRemoveCount(field) {
  const gridWrapper = document.getElementById("layout-grid");
  const table = gridWrapper ? gridWrapper.dataset.table : "";

  // Show “Checking…” immediately
  const removeCountP = document.getElementById("remove-count");
  removeCountP.textContent = "Checking…";
  document.getElementById("confirm-delete-checkbox").classList.add("hidden");
  document.getElementById("remove-submit-btn").disabled = true;

  // One-off fetch for this field
  fetch(`/${table}/count-nonnull?field=${field}`)
    .then(res => res.json())
    .then(data => {
      const count = data.count || 0;
      updateRemoveInfo(count);
    })
    .catch(() => {
      updateRemoveInfo(0);
    });
}

// Enable “Remove” button only if the confirmation checkbox is checked
function toggleRemoveButton() {
  const confirmCheckbox = document.getElementById("confirm-delete-checkbox");
  const removeBtn = document.getElementById("remove-submit-btn");
  removeBtn.disabled = !confirmCheckbox.checked;
}

function updateRemoveInfo(count) {
  const removeInfoDiv = document.getElementById("remove-info");
  const removeCountP = document.getElementById("remove-count");
  const checkboxLabel = document.getElementById("checkbox-label");
  const confirmCheckbox = document.getElementById("confirm-delete-checkbox");
  const removeBtn = document.getElementById("remove-submit-btn");

  if (count > 0) {
    removeCountP.textContent = `${count} record(s) will be deleted.`;
    checkboxLabel.textContent = `Confirm deletion of ${count} record(s)`;
    confirmCheckbox.checked = false;
    confirmCheckbox.classList.remove("hidden");
    removeInfoDiv.classList.remove("hidden");
    removeBtn.disabled = true;
  } else {
    removeCountP.textContent = "No values to delete for this field.";
    confirmCheckbox.classList.add("hidden");
    removeInfoDiv.classList.remove("hidden");
    removeBtn.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initEditFieldsTabs();
});
