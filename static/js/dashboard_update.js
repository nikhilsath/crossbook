document.addEventListener('DOMContentLoaded', () => {
  const updateBtn = document.getElementById('dashboard_update');
  if (updateBtn) {
    updateBtn.addEventListener('click', () => {
      window.location.reload();
    });
  }
});
