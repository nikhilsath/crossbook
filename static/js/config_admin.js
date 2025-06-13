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
});

