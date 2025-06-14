// Dashboard chart rendering

document.addEventListener('DOMContentLoaded', () => {
  const FLOWBITE_COLORS = [
    '#2563eb', // blue-600
    '#db2777', // pink-600
    '#059669', // emerald-600
    '#f59e0b', // amber-500
    '#8b5cf6', // violet-500
    '#ef4444'  // red-500
  ];

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

    const { chart_type: type = 'bar', x_field, y_field, aggregation, field, orientation } = cfg;
    const canvas = widget.querySelector('canvas') || document.createElement('canvas');
    if (!canvas.parentElement) widget.appendChild(canvas);

    if (type === 'pie') {
      if (!x_field) return;
      const [table, field] = x_field.split(':');
      try {
        const res = await fetch(`/${table}/field-distribution?field=${encodeURIComponent(field)}`);
        const data = await res.json();
        const labels = Object.keys(data);
        const values = Object.values(data);
        const colors = labels.map((_, i) => `hsl(${(i * 40) % 360},70%,60%)`);
        new Chart(canvas, {
          type: 'pie',
          data: { labels, datasets: [{ data: values, backgroundColor: colors }] },
          options: { responsive: true, maintainAspectRatio: false }
        });
      } catch (err) {
        console.error('[dashboard_charts] pie data fetch error', err);
      }
      return;
    }

    if (type === 'bar' && field) {
      const [table, fld] = field.split(':');
      try {
        const res = await fetch(`/${table}/field-distribution?field=${encodeURIComponent(fld)}`);
        const data = await res.json();
        const labels = Object.keys(data);
        const values = Object.values(data);
        const colors = labels.map((_, i) => FLOWBITE_COLORS[i % FLOWBITE_COLORS.length]);
        new Chart(canvas, {
          type: 'bar',
          data: { labels, datasets: [{ data: values, backgroundColor: colors }] },
          options: { responsive: true, maintainAspectRatio: false, indexAxis: orientation === 'y' ? 'y' : 'x', plugins: { legend: { display: false } } }
        });
      } catch (err) {
        console.error('[dashboard_charts] bar data fetch error', err);
      }
      return;
    }

    if (type === 'line' && field) {
      const [table, fld] = field.split(':');
      try {
        const res = await fetch(`/${table}/field-distribution?field=${encodeURIComponent(fld)}`);
        const data = await res.json();
        const labels = Object.keys(data);
        const values = Object.values(data);
        new Chart(canvas, {
          type: 'line',
          data: { labels, datasets: [{ data: values, borderColor: FLOWBITE_COLORS[0], backgroundColor: 'rgba(37,99,235,0.2)', fill: false }] },
          options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
        });
      } catch (err) {
        console.error('[dashboard_charts] line data fetch error', err);
      }
      return;
    }

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
