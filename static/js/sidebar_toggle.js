const sidebar = document.getElementById('sidebar');
const collapseBtn = document.getElementById('sidebarCollapse');
collapseBtn.innerHTML = sidebar.classList.contains('hidden') ? '&raquo;' : '&laquo;';
function toggleSidebar() {
  sidebar.classList.toggle('md:block');
  collapseBtn.innerHTML = sidebar.classList.contains('hidden') ? '&raquo;' : '&laquo;';
}
collapseBtn.addEventListener('click', toggleSidebar);
