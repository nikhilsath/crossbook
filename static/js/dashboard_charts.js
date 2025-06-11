// Dashboard chart rendering

document.addEventListener('DOMContentLoaded', () => {
  const chartWidgets = document.querySelectorAll('[data-type="chart"]');
  chartWidgets.forEach(async widget => {
    const cfgText = widget.dataset.config;
    if (!cfgText) return;
    let cfg;
    try {
      cfg = JSON.parse(cfgText);
    } catch (err) {
      console.error('[dashboard_charts] Invalid config', err);
      return;
    }
    const { chart_type: type = 'bar', x_field, y_field, aggregation } = cfg;
    if (!x_field || !y_field || !aggregation) return;

    const fetchVal = spec => {
      const [table, field] = spec.split(':');
      const endpoint = aggregation === 'sum' ? 'sum-field' : 'count-nonnull';
      const key = aggregation === 'sum' ? 'sum' : 'count';
      return fetch(`/${table}/${endpoint}?field=${encodeURIComponent(field)}`)
        .then(r => r.json())
        .then(d => d[key] || 0)
        .catch(() => 0);
    };

    const values = await Promise.all([fetchVal(x_field), fetchVal(y_field)]);
    const labels = [x_field.split(':')[1], y_field.split(':')[1]];

    const canvas = widget.querySelector('canvas') || document.createElement('canvas');
    if (!canvas.parentElement) widget.appendChild(canvas);

    new Chart(canvas, {
      type: type,
      data: {
        labels: labels,
        datasets: [{
          label: aggregation === 'count' ? 'Count' : 'Sum',
          data: values,
          backgroundColor: ['#3b82f6', '#d946ef']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } }
      }
    });
  });
});
