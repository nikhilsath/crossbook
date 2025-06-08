export function openDashboardModal() {
  document.getElementById('dashboardModal').classList.remove('hidden');
}

export function closeDashboardModal() {
  document.getElementById('dashboardModal').classList.add('hidden');
}

window.openDashboardModal = openDashboardModal;
window.closeDashboardModal = closeDashboardModal;

