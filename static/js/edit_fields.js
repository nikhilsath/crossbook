let fieldTypes = null;

async function loadFieldTypes() {
  if (fieldTypes) return fieldTypes;
  try {
    const res = await fetch('/api/field-types');
    fieldTypes = await res.json();
  } catch {
    fieldTypes = {};
  }
  return fieldTypes;
}

document.addEventListener("DOMContentLoaded", async () => {
  const fieldTypeSelect = document.getElementById("field_type");
  const optionsContainer = document.getElementById("field_options_container");
  const fkSelectContainer = document.getElementById("fk_select_container");
  const addFieldForm = document.getElementById("add-field-form");
  const fieldNameInput = document.querySelector('#add-field-form input[name="field_name"]');

  if (!fieldTypeSelect) return;
  await loadFieldTypes();

  Object.keys(fieldTypes).forEach((t) => {
    const opt = document.createElement('option');
    opt.value = t;
    opt.textContent = t;
    fieldTypeSelect.appendChild(opt);
  });

  fieldTypeSelect.addEventListener("change", () => {
    const meta = fieldTypes[fieldTypeSelect.value] || {};

    if (optionsContainer) {
      optionsContainer.classList.toggle("hidden", !meta.allows_options);
    }

    if (fkSelectContainer) {
      fkSelectContainer.classList.toggle("hidden", !meta.allows_foreign_key);
    }
  });

  // Normalize field name: replace spaces with underscores as user types
  if (fieldNameInput) {
    const normalize = () => {
      fieldNameInput.value = fieldNameInput.value.replace(/\s+/g, '_');
    };
    fieldNameInput.addEventListener('input', normalize);
    fieldNameInput.addEventListener('blur', normalize);
  }

  // Ensure normalization on submit as well
  if (addFieldForm) {
    addFieldForm.addEventListener('submit', () => {
      const inp = addFieldForm.querySelector('input[name="field_name"]');
      if (inp) inp.value = inp.value.replace(/\s+/g, '_');
    });
  }
});
  


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
  const removeInfoDiv = document.getElementById("remove_info_section");
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
