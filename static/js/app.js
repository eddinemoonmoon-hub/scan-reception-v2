// PMD Reception — Main JS

// ─── PWA INSTALL ─────────────────────────────────────
var deferredPrompt = null;

window.addEventListener('beforeinstallprompt', function(e) {
  e.preventDefault();
  deferredPrompt = e;
  showInstallButton();
});

window.addEventListener('appinstalled', function() {
  hideInstallButton();
  deferredPrompt = null;
});

function showInstallButton() {
  var btn = document.getElementById('pwa-install-btn');
  if (btn) btn.classList.remove('hidden');
}

function hideInstallButton() {
  var btn = document.getElementById('pwa-install-btn');
  if (btn) btn.classList.add('hidden');
}

function installPWA() {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  deferredPrompt.userChoice.then(function(result) {
    deferredPrompt = null;
    hideInstallButton();
  });
}

// ─── TOAST ───────────────────────────────────────────
function showToast(msg, type) {
  type = type || 'info';
  var toast = document.getElementById('toast');
  var toastMsg = document.getElementById('toast-msg');
  var iconWrap = document.getElementById('toast-icon-wrap');
  if (!toast) return;

  var configs = {
    success: { bg: 'linear-gradient(135deg,#10B981,#059669)' },
    error:   { bg: 'linear-gradient(135deg,#EF4444,#DC2626)' },
    warning: { bg: 'linear-gradient(135deg,#F59E0B,#D97706)' },
    info:    { bg: 'linear-gradient(135deg,#2563EB,#1D4ED8)' }
  };

  var svgs = {
    success: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M20 6L9 17l-5-5" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    error:   '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M18 6L6 18M6 6l12 12" stroke="white" stroke-width="2.5" stroke-linecap="round"/></svg>',
    warning: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 9v4M12 17h.01" stroke="white" stroke-width="2" stroke-linecap="round"/></svg>',
    info:    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="white" stroke-width="2"/><path d="M12 8v4M12 16h.01" stroke="white" stroke-width="2" stroke-linecap="round"/></svg>'
  };

  var cfg = configs[type] || configs.info;
  iconWrap.style.background = cfg.bg;
  iconWrap.innerHTML = svgs[type] || svgs.info;
  toastMsg.textContent = msg;
  toast.classList.remove('hidden', 'show');
  void toast.offsetWidth;
  toast.classList.add('show');
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(function() {
    toast.classList.remove('show');
  }, 3000);
}

function formatQty(v) {
  var n = parseFloat(v) || 0;
  return n % 1 === 0 ? String(parseInt(n)) : n.toFixed(2);
}
