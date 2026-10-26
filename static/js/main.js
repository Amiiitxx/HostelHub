/**
 * HostelMS — Main JavaScript Utilities
 * Shared across all pages
 */

// ============================================================
// SIDEBAR TOGGLE
// ============================================================

const COLLAPSED_KEY = 'sidebar_collapsed';

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('mainContent');
  const topbar = document.getElementById('topbar');
  const isMobile = window.innerWidth <= 768;

  if (isMobile) {
    sidebar.classList.toggle('mobile-open');
    document.getElementById('sidebarOverlay').classList.toggle('active');
  } else {
    const collapsed = sidebar.classList.toggle('collapsed');
    mainContent.classList.toggle('sidebar-collapsed', collapsed);
    topbar.classList.toggle('sidebar-collapsed', collapsed);
    localStorage.setItem(COLLAPSED_KEY, collapsed ? '1' : '0');
  }
}

function closeMobileSidebar() {
  document.getElementById('sidebar').classList.remove('mobile-open');
  document.getElementById('sidebarOverlay').classList.remove('active');
}

// Restore sidebar state on desktop
document.addEventListener('DOMContentLoaded', () => {
  if (window.innerWidth > 768 && localStorage.getItem(COLLAPSED_KEY) === '1') {
    document.getElementById('sidebar').classList.add('collapsed');
    document.getElementById('mainContent').classList.add('sidebar-collapsed');
    document.getElementById('topbar').classList.add('sidebar-collapsed');
  }
});

// ============================================================
// PREMIUM TOAST NOTIFICATIONS
// ============================================================

// Map type → Bootstrap Icon class
const TOAST_ICONS = {
  success: 'bi bi-check-circle-fill',
  error:   'bi bi-x-circle-fill',
  warning: 'bi bi-exclamation-triangle-fill',
  info:    'bi bi-info-circle-fill',
};

const TOAST_TITLES = {
  success: 'Success',
  error:   'Error',
  warning: 'Warning',
  info:    'Info',
};

/**
 * Show a premium slide-in toast notification.
 * @param {string} message  Body text
 * @param {string} type     'success' | 'error' | 'warning' | 'info'
 * @param {number} duration Milliseconds before auto-dismiss (default 4000)
 */
function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const safeType  = TOAST_ICONS[type] ? type : 'info';
  const iconClass = TOAST_ICONS[safeType];
  const title     = TOAST_TITLES[safeType];

  const toast = document.createElement('div');
  toast.className = `toast ${safeType}`;
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'assertive');

  toast.innerHTML = `
    <div class="toast-icon"><i class="${iconClass}"></i></div>
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      <div class="toast-message">${message}</div>
    </div>
    <button class="toast-close" aria-label="Dismiss" onclick="dismissToast(this.closest('.toast'))">
      <i class="bi bi-x"></i>
    </button>
    <div class="toast-progress" style="animation-duration: ${duration}ms;"></div>
  `;

  container.appendChild(toast);

  // Auto-dismiss after duration
  const timer = setTimeout(() => dismissToast(toast), duration);

  // Pause progress bar on hover
  toast.addEventListener('mouseenter', () => {
    clearTimeout(timer);
    const bar = toast.querySelector('.toast-progress');
    if (bar) bar.style.animationPlayState = 'paused';
  });
  toast.addEventListener('mouseleave', () => {
    const bar = toast.querySelector('.toast-progress');
    if (bar) {
      // Estimate remaining time from scaleX
      const remaining = Math.max(500, duration * 0.25);
      bar.style.animationPlayState = 'running';
      setTimeout(() => dismissToast(toast), remaining);
    }
  });
}

function dismissToast(toast) {
  if (!toast || toast.classList.contains('hiding')) return;
  toast.classList.add('hiding');
  // Wait for slide-out animation (0.32s) then remove
  setTimeout(() => toast.remove(), 360);
}

// ============================================================
// CONFIRM MODAL
// ============================================================

let _confirmCallback = null;

function showConfirm(message, onConfirm, options = {}) {
  const modal = document.getElementById('confirmModal');
  const bsModal = bootstrap.Modal.getOrCreateInstance(modal);
  document.getElementById('confirmModalMessage').textContent = message;
  document.getElementById('confirmModalSubtext').textContent = options.subtext || 'This action cannot be undone.';
  document.getElementById('confirmModalTitle').textContent = options.title || 'Confirm Action';
  const btn = document.getElementById('confirmModalBtn');
  btn.textContent = options.btnText || 'Delete';
  btn.className = `btn btn-${options.btnClass || 'danger'}`;
  _confirmCallback = onConfirm;
  bsModal.show();
}

document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('confirmModalBtn');
  if (btn) {
    btn.addEventListener('click', () => {
      const bsModal = bootstrap.Modal.getInstance(document.getElementById('confirmModal'));
      if (bsModal) bsModal.hide();
      if (_confirmCallback) { _confirmCallback(); _confirmCallback = null; }
    });
  }
});

// ============================================================
// CSRF FETCH HELPER
// ============================================================

function getCsrfToken() {
  return document.cookie.split(';').map(c => c.trim()).find(c => c.startsWith('csrftoken='))?.split('=')[1] || '';
}

async function fetchPost(url, data = {}) {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
      'X-Requested-With': 'XMLHttpRequest',
    },
    body: JSON.stringify(data),
  });
  return response.json();
}

async function fetchGet(url, params = {}) {
  const qs = new URLSearchParams(params).toString();
  const fullUrl = qs ? `${url}?${qs}` : url;
  const response = await fetch(fullUrl, {
    headers: { 'X-Requested-With': 'XMLHttpRequest' },
  });
  return response.json();
}

// ============================================================
// TABLE LIVE SEARCH
// ============================================================

function initTableSearch(inputId, tableId, columns = null) {
  const input = document.getElementById(inputId);
  const table = document.getElementById(tableId);
  if (!input || !table) return;

  input.addEventListener('input', () => {
    const q = input.value.toLowerCase().trim();
    const rows = table.querySelectorAll('tbody tr');
    let visible = 0;

    rows.forEach(row => {
      const text = (columns
        ? [...row.querySelectorAll('td')].filter((_, i) => columns.includes(i)).map(td => td.textContent).join(' ')
        : row.textContent
      ).toLowerCase();
      const match = !q || text.includes(q);
      row.style.display = match ? '' : 'none';
      if (match) visible++;
    });

    // Show/hide empty state
    const emptyState = document.getElementById(tableId + '_empty');
    if (emptyState) emptyState.style.display = visible === 0 ? '' : 'none';
  });
}

// ============================================================
// SORTABLE TABLE HEADERS
// ============================================================

function initSortableTable(tableId) {
  const table = document.getElementById(tableId);
  if (!table) return;

  table.querySelectorAll('th.sortable').forEach((th, idx) => {
    th.addEventListener('click', () => {
      const tbody = table.querySelector('tbody');
      const rows = [...tbody.querySelectorAll('tr')];
      const dir = th.dataset.dir === 'asc' ? 'desc' : 'asc';
      th.dataset.dir = dir;

      // Clear other headers
      table.querySelectorAll('th.sortable').forEach(t => {
        t.dataset.dir = '';
        const icon = t.querySelector('.sort-icon');
        if (icon) icon.innerHTML = '↕';
      });

      const icon = th.querySelector('.sort-icon');
      if (icon) icon.innerHTML = dir === 'asc' ? '↑' : '↓';

      rows.sort((a, b) => {
        const aVal = a.querySelectorAll('td')[idx]?.textContent.trim() || '';
        const bVal = b.querySelectorAll('td')[idx]?.textContent.trim() || '';
        const aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
        const bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));
        if (!isNaN(aNum) && !isNaN(bNum)) {
          return dir === 'asc' ? aNum - bNum : bNum - aNum;
        }
        return dir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      });

      rows.forEach(row => tbody.appendChild(row));
    });
  });
}

// ============================================================
// FORM LOADING STATE
// ============================================================

function setFormLoading(formEl, loading = true) {
  const btn = formEl.querySelector('[type="submit"]');
  if (!btn) return;
  if (loading) {
    btn._originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="spinner"></span> Saving...';
    btn.disabled = true;
    formEl.querySelectorAll('input, select, textarea').forEach(el => el.disabled = true);
  } else {
    btn.innerHTML = btn._originalHTML || 'Save';
    btn.disabled = false;
    formEl.querySelectorAll('input, select, textarea').forEach(el => el.disabled = false);
  }
}

// ============================================================
// GLOBAL SEARCH (placeholder — modules override)
// ============================================================

function handleGlobalSearch(val) {
  // Can be extended by individual pages
}

// ============================================================
// DEPENDENT DROPDOWNS (for allocation: building→floor→room→bed)
// ============================================================

async function loadFloors(buildingId, floorSelect, roomSelect, bedSelect) {
  floorSelect.innerHTML = '<option value="">Loading...</option>';
  if (roomSelect) { roomSelect.innerHTML = '<option value="">Select Room</option>'; roomSelect.disabled = true; }
  if (bedSelect) { bedSelect.innerHTML = '<option value="">Select Bed</option>'; bedSelect.disabled = true; }
  if (!buildingId) { floorSelect.innerHTML = '<option value="">Select Floor</option>'; floorSelect.disabled = true; return; }
  try {
    const data = await fetchGet('/hostel/ajax/floors/', { building_id: buildingId });
    floorSelect.innerHTML = '<option value="">Select Floor</option>';
    data.floors.forEach(f => floorSelect.add(new Option(f.name, f.id)));
    floorSelect.disabled = false;
  } catch (e) {
    floorSelect.innerHTML = '<option value="">Error loading</option>';
  }
}

async function loadRooms(floorId, roomSelect, bedSelect) {
  roomSelect.innerHTML = '<option value="">Loading...</option>';
  if (bedSelect) { bedSelect.innerHTML = '<option value="">Select Bed</option>'; bedSelect.disabled = true; }
  if (!floorId) { roomSelect.innerHTML = '<option value="">Select Room</option>'; roomSelect.disabled = true; return; }
  try {
    const data = await fetchGet('/hostel/ajax/rooms/', { floor_id: floorId });
    roomSelect.innerHTML = '<option value="">Select Room</option>';
    data.rooms.forEach(r => roomSelect.add(new Option(r.name, r.id)));
    roomSelect.disabled = false;
  } catch (e) {
    roomSelect.innerHTML = '<option value="">Error loading</option>';
  }
}

async function loadBeds(roomId, bedSelect) {
  bedSelect.innerHTML = '<option value="">Loading...</option>';
  if (!roomId) { bedSelect.innerHTML = '<option value="">Select Bed</option>'; bedSelect.disabled = true; return; }
  try {
    const data = await fetchGet('/hostel/ajax/beds/', { room_id: roomId });
    bedSelect.innerHTML = '<option value="">Select Bed</option>';
    data.beds.forEach(b => bedSelect.add(new Option(b.name, b.id)));
    bedSelect.disabled = data.beds.length === 0;
  } catch (e) {
    bedSelect.innerHTML = '<option value="">Error loading</option>';
  }
}

// ============================================================
// CHART.JS DEFAULT CONFIG
// ============================================================

Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#64748B';

const CHART_COLORS = {
  primary: '#4F46E5',
  success: '#059669',
  warning: '#D97706',
  danger: '#DC2626',
  info: '#0284C7',
  muted: '#94A3B8',
  primaryLight: 'rgba(79,70,229,0.1)',
  successLight: 'rgba(5,150,105,0.1)',
  warningLight: 'rgba(217,119,6,0.1)',
  dangerLight: 'rgba(220,38,38,0.1)',
};

// ============================================================
// DATE FILTER TABS
// ============================================================

function initDateFilterTabs(containerId, onChange) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.querySelectorAll('.date-filter-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      container.querySelectorAll('.date-filter-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      if (onChange) onChange(tab.dataset.period);
    });
  });
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function formatNumber(n) {
  return n?.toLocaleString() ?? '0';
}

function formatCurrency(n) {
  return '₹' + (n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 });
}

function debounce(fn, ms = 300) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), ms);
  };
}
