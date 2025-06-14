function updateConditionalFields() {
  const handler = document.querySelector('[name="handler_type"]');
  const maxSize = document.querySelector('[name="max_file_size"]');
  const backup = document.querySelector('[name="backup_count"]');
  const whenInterval = document.querySelector('[name="when_interval"]');
  const intervalCount = document.querySelector('[name="interval_count"]');
  const maxSizeContainer = document.querySelector('[data-field="max_file_size"]');
  const backupContainer = document.querySelector('[data-field="backup_count"]');
  const whenIntervalContainer = document.querySelector('[data-field="when_interval"]');
  const intervalCountContainer = document.querySelector('[data-field="interval_count"]');
  if (!handler) return;

  const clearReq = el => {
    if (!el) return;
    el.required = false;
    const label = document.querySelector('label[for="' + el.name + '"]');
    if (label) label.classList.remove('text-red-600');
  };
  [maxSize, backup, whenInterval, intervalCount].forEach(clearReq);
  [maxSizeContainer, backupContainer, whenIntervalContainer, intervalCountContainer].forEach(c => {
    if (c) c.classList.add('hidden');
  });

  const markReq = el => {
    if (!el) return;
    el.required = true;
    const label = document.querySelector('label[for="' + el.name + '"]');
    if (label) label.classList.add('text-red-600');
  };

  const type = handler.value;
  if (type === 'rotating') {
    markReq(maxSize);
    markReq(backup);
    if (maxSizeContainer) maxSizeContainer.classList.remove('hidden');
    if (backupContainer) backupContainer.classList.remove('hidden');
  } else if (type === 'timed') {
    markReq(backup);
    markReq(whenInterval);
    markReq(intervalCount);
    if (backupContainer) backupContainer.classList.remove('hidden');
    if (whenIntervalContainer) whenIntervalContainer.classList.remove('hidden');
    if (intervalCountContainer) intervalCountContainer.classList.remove('hidden');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const handler = document.querySelector('[name="handler_type"]');
  if (handler) {
    handler.addEventListener('change', updateConditionalFields);
    updateConditionalFields();
  }
});
