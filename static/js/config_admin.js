// Handle form submission for JSON config items

function initLayoutDefaultsForms() {
  document.querySelectorAll('form[data-json-key="layout_defaults"]').forEach(form => {
    form.addEventListener('submit', e => {
      const width = {};
      form.querySelectorAll('input[name^="width."]').forEach(inp => {
        const key = inp.name.split('.')[1];
        width[key] = parseFloat(inp.value) || 0;
      });
      const height = {};
      form.querySelectorAll('input[name^="height."]').forEach(inp => {
        const key = inp.name.split('.')[1];
        height[key] = parseFloat(inp.value) || 0;
      });
      const hidden = form.querySelector('input[name="value"]');
      if (hidden) {
        hidden.value = JSON.stringify({ width, height });
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initLayoutDefaultsForms();
  // Handle title field selection radios
  document.querySelectorAll('input.title-radio').forEach(r => {
    r.addEventListener('change', async (e) => {
      const input = e.currentTarget;
      if (!input.checked) return;
      const table = input.dataset.table;
      const field = input.value;
      try {
        const resp = await fetch(`/admin/fields/${encodeURIComponent(table)}/title`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ field })
        });
        const data = await resp.json().catch(() => ({}));
        if (!resp.ok || !data.success) {
          alert('Failed to set title field');
        }
      } catch (err) {
        console.error('Title set failed', err);
        alert('Failed to set title field');
      }
    });
  });
});
