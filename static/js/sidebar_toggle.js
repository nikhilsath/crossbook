const sidebar = document.getElementById('sidebar');
const collapseBtn = document.getElementById('sidebarCollapse');

function setToggleIcon() {
  collapseBtn.innerHTML = sidebar.classList.contains('md:block') ? '&laquo;' : '&raquo;';
}

function toggleSidebar() {
  sidebar.classList.toggle('md:block');
  setToggleIcon();
}

setToggleIcon();
collapseBtn.addEventListener('click', toggleSidebar);
