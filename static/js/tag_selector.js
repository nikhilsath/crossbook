{% macro render_tag_selector(field, value, table, get_field_options) %}
  <form method="POST" action="{{ url_for('records.update_field', table=table, record_id=request.view_args['record_id']) }}" class="relative w-full" data-multiselect-dropdown onsubmit="event.preventDefault();">
    <input type="hidden" name="field" value="{{ field }}">
    {% set selected_options = (value or '').split(', ') %}

    <div class="flex flex-wrap gap-1 mb-2 tag-container">
      {% for tag in selected_options if tag %}
        <span class="inline-flex items-center bg-teal-100 text-teal-700 text-xs px-2 py-1 rounded-full">
          {{ tag }}
          <button type="button" class="ml-1 text-teal-600 hover:text-red-500" onclick="this.closest('form').querySelector('input[value=' + JSON.stringify('{{ tag }}') + ']').checked = false; submitMultiSelectAuto(this.closest('form'))">×</button>
        </span>
      {% endfor %}
    </div>

    <button type="button" class="dropdown-btn" onclick="this.nextElementSibling.classList.toggle('hidden')">
      Choose Tags
    </button>

    <div class="absolute z-10 mt-1 w-full popover-dark hidden max-h-64 overflow-y-auto space-y-1" data-options>
      <input type="text" placeholder="Search..." class="form-input text-sm mb-2" oninput="const v=this.value.toLowerCase();[...this.parentElement.querySelectorAll('label')].forEach(l => l.classList.toggle('hidden', !l.textContent.toLowerCase().includes(v)))">
      {% for option in get_field_options(table, field) %}
        <label class="flex items-center space-x-2">
          <input
            type="checkbox"
            name="new_value[]"
            value="{{ option }}"
            {% if option in selected_options %}checked{% endif %}
            onchange="submitMultiSelectAuto(this.form)"
            class="rounded border-gray-300 text-teal-600 shadow-sm focus:ring-teal-600"
          >
          <span class="text-sm">{{ option }}</span>
        </label>
      {% endfor %}
    </div>
  </form>
{% endmacro %}
