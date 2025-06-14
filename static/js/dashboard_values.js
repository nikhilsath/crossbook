// Dashboard value widget rendering

document.addEventListener('DOMContentLoaded', () => {
  const valueWidgets = document.querySelectorAll('[data-type="value"]');
  valueWidgets.forEach(async widget => {
    const cfgText = widget.dataset.config;
    if (!cfgText) return;
    let cfg;
    try {
      cfg = JSON.parse(cfgText);
    } catch (err) {
      console.error('[dashboard_values] Invalid config', err);
      return;
    }

    const resultEl = widget.querySelector('.value-result');
    if (!resultEl) return;

    async function fetchValue(table, field, op) {
      const endpoint = op === 'sum' ? 'sum-field' : 'count-nonnull';
      const key = op === 'sum' ? 'sum' : 'count';
      try {
        const res = await fetch(`/${table}/${endpoint}?field=${encodeURIComponent(field)}`);
        const data = await res.json();
        return data[key] || 0;
      } catch (e) {
        console.error('[dashboard_values] fetch error', e);
        return 0;
      }
    }

    if (cfg.operation === 'sum' || cfg.operation === 'count') {
      const { table, field } = cfg;
      resultEl.textContent = '...';
      const val = await fetchValue(table, field, cfg.operation);
      resultEl.textContent = val;
      return;
    }

    if (cfg.operation === 'math') {
      const { math_operation, field1, field2, agg1 = 'sum', agg2 = 'sum' } = cfg;
      if (!field1 || !math_operation) return;
      resultEl.textContent = '...';
      if (math_operation === 'average') {
        const [t, f] = field1.split(':');
        const total = await fetchValue(t, f, 'sum');
        const count = await fetchValue(t, f, 'count');
        resultEl.textContent = count ? total / count : 0;
        return;
      }
      if (!field2) return;
      const [t1, f1] = field1.split(':');
      const [t2, f2] = field2.split(':');
      const v1 = await fetchValue(t1, f1, agg1);
      const v2 = await fetchValue(t2, f2, agg2);
      let result = 0;
      switch (math_operation) {
        case 'add':
          result = v1 + v2; break;
        case 'subtract':
          result = v1 - v2; break;
        case 'multiply':
          result = v1 * v2; break;
        case 'divide':
          result = v1 / (v2 || 1); break;
      }
      resultEl.textContent = result;
    }
  });
});
