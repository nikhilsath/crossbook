const sidebar = document.getElementById('sidebar');
const collapseBtn = document.getElementById('sidebarCollapse');
const sidebarHandle = document.getElementById('sidebar-handle');
const contentWrapper = document.getElementById('content-wrapper');
const pageHeader = document.getElementById('page-header');

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

function updateLayout() {
  if (window.innerWidth >= 768 && isSidebarOpen()) {
    contentWrapper.classList.add('md:ml-56');
    pageHeader.classList.add('md:pl-56');
  } else {
    contentWrapper.classList.remove('md:ml-56');
    pageHeader.classList.remove('md:pl-56');
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
  updateLayout();
}

setToggleIcon();
updateHandleVisibility();
updateLayout();
collapseBtn.addEventListener('click', toggleSidebar);
sidebarHandle.addEventListener('click', toggleSidebar);
window.addEventListener('resize', updateLayout);
