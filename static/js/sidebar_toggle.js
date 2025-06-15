const sidebar = document.getElementById('sidebar');
const collapseBtn = document.getElementById('sidebarCollapse');
const sidebarHandle = document.getElementById('sidebar-handle');

function isSidebarOpen() {
  if (window.innerWidth < 768) {
    return !sidebar.classList.contains('hidden');
  }
  return sidebar.classList.contains('md:block');
}

function setToggleIcon() {
  collapseBtn.innerHTML = isSidebarOpen() ? '&laquo;' : '&raquo;';
}

function updateHandleVisibility() {
  if (isSidebarOpen()) {
    sidebarHandle.classList.add('hidden');
  } else {
    sidebarHandle.classList.remove('hidden');
  }
}

function toggleSidebar() {
  if (window.innerWidth < 768) {
    sidebar.classList.toggle('hidden');
  } else {
    sidebar.classList.toggle('md:block');
  }
  setToggleIcon();
  updateHandleVisibility();
}

setToggleIcon();
updateHandleVisibility();
collapseBtn.addEventListener('click', toggleSidebar);
sidebarHandle.addEventListener('click', toggleSidebar);
