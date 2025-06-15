const sidebar = document.getElementById('sidebar');
const collapseBtn = document.getElementById('sidebarCollapse');
const sidebarHandle = document.getElementById('sidebar-handle');

function setToggleIcon() {
  collapseBtn.innerHTML = sidebar.classList.contains('md:block') ? '&laquo;' : '&raquo;';
}

function updateHandleVisibility() {
  if (sidebar.classList.contains('md:block')) {
    sidebarHandle.classList.add('hidden');
  } else {
    sidebarHandle.classList.remove('hidden');
  }
}

function toggleSidebar() {
  sidebar.classList.toggle('md:block');
  setToggleIcon();
  updateHandleVisibility();
}

setToggleIcon();
updateHandleVisibility();
collapseBtn.addEventListener('click', toggleSidebar);
sidebarHandle.addEventListener('click', toggleSidebar);
