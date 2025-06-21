// Dashboard chart rendering

document.addEventListener('DOMContentLoaded', () => {
  const FLOWBITE_COLORS = [
    '#0D9488', // teal
    '#7C3AED'  // purple
  ];

  function attachResize(widget, chart) {
    if (!chart) return;
    const ro = new ResizeObserver(() => {
      try { chart.resize(); } catch (e) { console.error('chart resize error', e); }
    });
    ro.observe(widget);
  }

  async function refreshChartWidget(widget) {
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
    const hideLegend = widget._styling && widget._styling.hideLegend;
    const canvas = widget.querySelector('canvas') || document.createElement('canvas');
    if (!canvas.parentElement) widget.appendChild(canvas);
    if (widget._chart) {
      try { widget._chart.destroy(); } catch (e) { console.error('chart destroy error', e); }
    }
    let chartInstance = null;

    if (type === 'pie') {
      if (!x_field) return;
      const [table, fieldName] = x_field.split(':');
      try {
        const res = await fetch(`/${table}/field-distribution?field=${encodeURIComponent(fieldName)}`);
        const data = await res.json();
        const labels = Object.keys(data);
        const values = Object.values(data);
        const colors = labels.map((_, i) => `hsl(${(i * 40) % 360},70%,60%)`);
        chartInstance = new Chart(canvas, {
          type: 'pie',
          data: { labels, datasets: [{ data: values, backgroundColor: colors }] },
          options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: !hideLegend } } }
        });
      } catch (err) {
        console.error('[dashboard_charts] pie data fetch error', err);
      }
      widget._chart = chartInstance;
      attachResize(widget, chartInstance);
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
        chartInstance = new Chart(canvas, {
          type: 'bar',
          data: { labels, datasets: [{ data: values, backgroundColor: colors }] },
          options: { responsive: true, maintainAspectRatio: false, indexAxis: orientation === 'y' ? 'y' : 'x', plugins: { legend: { display: !hideLegend } } }
        });
      } catch (err) {
        console.error('[dashboard_charts] bar data fetch error', err);
      }
      widget._chart = chartInstance;
      attachResize(widget, chartInstance);
      return;
    }

    if (type === 'line' && field) {
      const [table, fld] = field.split(':');
      try {
        const res = await fetch(`/${table}/field-distribution?field=${encodeURIComponent(fld)}`);
        const data = await res.json();
        const labels = Object.keys(data);
        const values = Object.values(data);
        chartInstance = new Chart(canvas, {
          type: 'line',
          data: { labels, datasets: [{ data: values, borderColor: FLOWBITE_COLORS[0], backgroundColor: 'rgba(13,148,136,0.2)', fill: false }] },
          options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: !hideLegend } } }
        });
      } catch (err) {
        console.error('[dashboard_charts] line data fetch error', err);
      }
      widget._chart = chartInstance;
      attachResize(widget, chartInstance);
      return;
    }

    if (!x_field || !y_field || !aggregation) return;

    const fetchVal = spec => {
      const [table, fieldName] = spec.split(':');
      const endpoint = aggregation === 'sum' ? 'sum-field' : 'count-nonnull';
      const key = aggregation === 'sum' ? 'sum' : 'count';
      return fetch(`/${table}/${endpoint}?field=${encodeURIComponent(fieldName)}`)
        .then(r => r.json())
        .then(d => d[key] || 0)
        .catch(() => 0);
    };

    const values = await Promise.all([fetchVal(x_field), fetchVal(y_field)]);
    const labels = [x_field.split(':')[1], y_field.split(':')[1]];

    chartInstance = new Chart(canvas, {
      type: type,
      data: {
        labels: labels,
        datasets: [{
          label: aggregation === 'count' ? 'Count' : 'Sum',
          data: values,
          backgroundColor: [FLOWBITE_COLORS[0], FLOWBITE_COLORS[1]]
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: !hideLegend } }
      }
    });
    widget._chart = chartInstance;
    attachResize(widget, chartInstance);
  }

  const chartWidgets = document.querySelectorAll('[data-type="chart"]');
  chartWidgets.forEach(widget => refreshChartWidget(widget));
  window.refreshChartWidget = refreshChartWidget;
});
