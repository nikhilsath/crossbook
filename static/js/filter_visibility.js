document.addEventListener("DOMContentLoaded", () => {
    // Elements
    const toggleBtn  = document.getElementById("toggle-filters");
    const dropdown   = document.getElementById("filter-dropdown");
    const clearBtn   = document.getElementById("reset-filters");
  
    // Utility: get columns currently visible
    const getSelectedFields = () =>
      Array.from(document.querySelectorAll(".column-toggle"))
           .filter(cb => cb.checked)
           .map(cb => cb.value);
  
    // Update URL based on checked filters and reload
    function updateFilters() {
      const params = new URLSearchParams(window.location.search);
  
      // Remove existing filter params for all visible fields
      getSelectedFields().forEach(f => params.delete(f));
  
      // Add back only the ones currently checked
      Array.from(dropdown.querySelectorAll(".filter-toggle"))
        .filter(cb => cb.checked)
        .forEach(cb => params.set(cb.value, ""));
  
      window.location.search = params.toString();
    }
  
    // Populate the dropdown with checkboxes for each visible column
    function populateFilterDropdown() {
      dropdown.innerHTML = "";
      const params = new URLSearchParams(window.location.search);
  
      getSelectedFields().forEach(field => {
        const label = document.createElement("label");
        label.classList.add("flex", "items-center", "space-x-2");
  
        const input = document.createElement("input");
        input.type = "checkbox";
        input.classList.add("filter-toggle");
        input.value = field;
        if (params.has(field)) input.checked = true;
  
        input.addEventListener("change", updateFilters);
  
        const span = document.createElement("span");
        span.classList.add("text-sm");
        span.textContent = field;
  
        label.append(input, span);
        dropdown.append(label);
      });
    }
  
    // Debounce utility: delays fn until after wait ms of inactivity
    function debounce(fn, wait) {
      let timer = null;
      return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), wait);
      };
    }
  
    // Handle debounced text input: update URL and reload
    function onTextFilterInput(e) {
      const input = e.target;
      const params = new URLSearchParams(window.location.search);
  
      params.set(input.name, input.value);
      window.location.search = params.toString();
    }
  
    // Bind debounce to all active text filter inputs
    function bindDebounceToFilters() {
      const inputs = document.querySelectorAll("#filter-container input[type='text']");
      inputs.forEach(input =>
        input.addEventListener("input", debounce(onTextFilterInput, 400))
      );
    }

    function onNumberFilterChange(e) {
      const input = e.target;
      const params = new URLSearchParams(window.location.search);
      if (input.value === "") {
        params.delete(input.name);
      } else {
        params.set(input.name, input.value);
      }
      window.location.search = params.toString();
    }

  function bindNumberFilters() {
    document
      .querySelectorAll("#filter-container input[type='number']")
      .forEach(input => input.addEventListener("change", onNumberFilterChange));
  }

  function onDateFilterChange(e) {
    const input = e.target;
    const params = new URLSearchParams(window.location.search);
    if (input.value === "") {
      params.delete(input.name);
    } else {
      params.set(input.name, input.value);
    }
    window.location.search = params.toString();
  }

  function bindDateFilters() {
    document
      .querySelectorAll("#filter-container input[type='date']")
      .forEach(input => input.addEventListener("change", onDateFilterChange));
  }
  
    // Handle operator dropdown changes
    function setOperatorTitle(sel) {
      const opt = sel.options[sel.selectedIndex];
      if (opt && opt.title) sel.title = opt.title;
    }

    function onOperatorChange(e) {
      const sel = e.target;
      const params = new URLSearchParams(window.location.search);
      const field = sel.name.replace(/_op$/, '');
      const val   = params.get(field) || "";

      params.set(sel.name, sel.value);
      params.set(field, val);
      window.location.search = params.toString();
    }
  
    // Bind operator change listeners
    function bindOperatorListeners() {
      const ops = document.querySelectorAll("#filter-container select.operator-select");
      ops.forEach(sel => {
        setOperatorTitle(sel);
        sel.addEventListener("change", e => {
          setOperatorTitle(sel);
          onOperatorChange(e);
        });
      });
    }
    // Bind change handlers for non-operator selects (i.e. our select filters)
    document.querySelectorAll("#filter-container select:not(.operator-select)")
    .forEach(sel =>
        sel.addEventListener("change", e => {
        const params = new URLSearchParams(window.location.search);
        params.set(sel.name, sel.value);
        window.location.search = params.toString();
        })
    );

  
    // Toggle dropdown visibility
    toggleBtn.addEventListener("click", e => {
      e.stopPropagation();
      dropdown.classList.toggle("hidden");
      populateFilterDropdown();
    });
    document.addEventListener("click", () => dropdown.classList.add("hidden"));
    dropdown.addEventListener("click", e => e.stopPropagation());
  
    // Clear filters button: remove all filter params & reload
    clearBtn.addEventListener("click", () => {
      const params = new URLSearchParams(window.location.search);
      getSelectedFields().forEach(f => params.delete(f));
      window.location.search = params.toString();
    });
  
    // Rebuild dropdown whenever column visibility changes
    document.querySelectorAll(".column-toggle").forEach(cb => {
      cb.addEventListener("change", () => setTimeout(populateFilterDropdown, 0));
    });
  
    // Initial binding for inputs and operators
    bindDebounceToFilters();
    bindOperatorListeners();
    bindNumberFilters();
    bindDateFilters();
  });
  
    // Multi-select popover logic
  function updateMultiSelect(field, values, mode) {
    const params = new URLSearchParams(window.location.search);
    // Remove all previous entries for this field
    params.delete(field);
    params.delete(field + "_mode");
    // Add back each selected value
    values.forEach(v => params.append(field, v));
    if (mode) params.set(field + "_mode", mode);
    window.location.search = params.toString();
  }

  function bindMultiSelectPopovers() {
    // Toggle popover open/close
    document.querySelectorAll(".multi-select-chip").forEach(btn => {
      const field = btn.dataset.field;
      const pop = document.querySelector(`.multi-select-popover[data-field="${field}"]`);

      btn.addEventListener("click", e => {
        e.stopPropagation();
        // close others
        document.querySelectorAll(".multi-select-popover")
                .forEach(p => p !== pop && p.classList.add("hidden"));
        pop.classList.toggle("hidden");
      });

      // prevent closing when interacting within the popover
      pop.addEventListener("click", e => e.stopPropagation());

      const modeSel = pop.querySelector(".multi-select-mode");

      function handleChange() {
        const selected = Array.from(
          pop.querySelectorAll(".multi-select-option:checked")
        ).map(c => c.value);
        updateMultiSelect(field, selected, modeSel ? modeSel.value : "any");
      }

      pop.querySelectorAll(".multi-select-option").forEach(cb => {
        cb.addEventListener("change", handleChange);
      });
      if (modeSel) modeSel.addEventListener("change", handleChange);
    });

    // Close all popovers when clicking outside
    document.addEventListener("click", () => {
      document.querySelectorAll(".multi-select-popover")
              .forEach(p => p.classList.add("hidden"));
    });
  }

  // call it after your other binds
  bindMultiSelectPopovers();

  function updateSelectMulti(field, values) {
    const params = new URLSearchParams(window.location.search);
    params.delete(field);
    params.delete(field + "_op");
    values.forEach(v => params.append(field, v));
    if (values.length) params.set(field + "_op", "equals");
    window.location.search = params.toString();
  }

  function bindSelectMulti() {
    document.querySelectorAll(".select-multi-filter").forEach(div => {
      const field = div.dataset.field;
      const boxes = div.querySelectorAll(".select-multi-option");
      boxes.forEach(cb =>
        cb.addEventListener("change", () => {
          const selected = Array.from(boxes)
            .filter(b => b.checked)
            .map(b => b.value);
          updateSelectMulti(field, selected);
        })
      );
    });
  }

  bindSelectMulti();
