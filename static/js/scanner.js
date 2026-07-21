// PMD Reception — Scanner JS
// Honeywell EDA51 PDA - With Offline Support

var currentArticle = null;
var isPaused = false;
var scanCooldown = false;
var scanTimer = null;
var isOffline = false;

window.addEventListener("DOMContentLoaded", function() {
  syncArticles().then(function() {
    getArticleCacheCount().then(function(count) {
      console.log('[Scanner] Local article cache: ' + count + ' articles');
    });
  });

  loadSessionInfo();
  setupScanner();
  setupOfflineDetection();
});

// ─────────────────────────────────────────
// OFFLINE DETECTION
// ─────────────────────────────────────────

function setupOfflineDetection() {
  isOffline = !navigator.onLine;
  updateOfflineBanner(isOffline);

  window.addEventListener('online', function() {
    isOffline = false;
    updateOfflineBanner(false);
    showToast('Connexion retablie', 'success');
    drainQueue();
  });

  window.addEventListener('offline', function() {
    isOffline = true;
    updateOfflineBanner(true);
    showToast('Hors ligne - scans sauvegardes localement', 'warning');
  });

  getPendingCount().then(function(count) {
    if (count > 0 && navigator.onLine) {
      showToast(count + ' scan(s) en attente de sync', 'warning');
      drainQueue();
    }
  });
}

function updateOfflineBanner(offline) {
  var banner = document.getElementById('offline-banner');
  if (!banner) return;
  if (offline) {
    banner.classList.remove('hidden');
  } else {
    banner.classList.add('hidden');
  }
}

// ─────────────────────────────────────────
// SESSION
// ─────────────────────────────────────────

function loadSessionInfo() {
  fetch("/api/current-reception")
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (!data.active) {
        var ref = localStorage.getItem('pmd_reception_ref');
        if (ref && !navigator.onLine) {
          document.getElementById("header-ref").textContent = ref;
          return;
        }
        window.location.href = "/";
        return;
      }
      localStorage.setItem('pmd_reception_ref', data.reference);
      localStorage.setItem('pmd_reception_id', data.reception_id);
      document.getElementById("header-ref").textContent = data.reference;
      var badge = document.getElementById("badge-count");
      if (data.total_lignes > 0) {
        badge.textContent = data.total_lignes;
        badge.classList.remove("hidden");
      }
    })
    .catch(function() {
      var ref = localStorage.getItem('pmd_reception_ref');
      document.getElementById("header-ref").textContent = ref || "Hors ligne";
    });
}

// ─────────────────────────────────────────
// SCANNER SETUP
// ─────────────────────────────────────────

function setupScanner() {
  var manualInput = document.getElementById("manual-input");
  var manualSearchInput = document.getElementById("manual-search-input");

  setTimeout(function() { manualInput.focus(); }, 500);

  setInterval(function() {
    var qtyPanel = document.getElementById("qty-panel");
    var searchActive = document.activeElement === manualSearchInput;
    if (!isPaused && !qtyPanel.classList.contains("visible") && !searchActive) {
      manualInput.focus();
    }
  }, 1000);

  // Method 1: detect \n or \r (Honeywell suffix)
  manualInput.addEventListener("input", function() {
    var val = manualInput.value;
    if (val.indexOf("\n") !== -1 || val.indexOf("\r") !== -1) {
      var barcode = val.replace(/[\r\n]/g, "").trim();
      manualInput.value = "";
      if (barcode.length >= 4) processBarcode(barcode);
      return;
    }
    // Method 2: auto-submit after 150ms pause
    clearTimeout(scanTimer);
    scanTimer = setTimeout(function() {
      var barcode = manualInput.value.trim();
      if (barcode.length >= 4) {
        manualInput.value = "";
        processBarcode(barcode);
      }
    }, 150);
  });

  // Method 3: Enter key fallback
  manualInput.addEventListener("keydown", function(e) {
    if (e.key === "Enter" || e.keyCode === 13) {
      e.preventDefault();
      clearTimeout(scanTimer);
      var barcode = manualInput.value.trim();
      manualInput.value = "";
      if (barcode.length >= 4) processBarcode(barcode);
    }
  });
}

// ─────────────────────────────────────────
// BARCODE PROCESSING
// ─────────────────────────────────────────

function processBarcode(barcode) {
  if (isPaused || scanCooldown) return;
  isPaused = true;
  scanCooldown = true;

  localLookup(barcode)
    .then(function(data) {
      if (data.found) {
        showFound(data.article);
      } else {
        if (navigator.onLine) {
          return fetch("/api/lookup?barcode=" + encodeURIComponent(barcode))
            .then(function(r) { return r.json(); })
            .then(function(serverData) {
              if (serverData.found) {
                showFound(serverData.article);
              } else {
                showNotFound(barcode);
              }
            });
        } else {
          showNotFound(barcode);
        }
      }
    })
    .catch(function() {
      if (navigator.onLine) {
        fetch("/api/lookup?barcode=" + encodeURIComponent(barcode))
          .then(function(r) { return r.json(); })
          .then(function(data) {
            if (data.found) {
              showFound(data.article);
            } else {
              showNotFound(barcode);
            }
          })
          .catch(function() {
            showToast("Erreur reseau", "error");
            resumeScanning();
          });
      } else {
        showToast("Hors ligne - article introuvable", "error");
        resumeScanning();
      }
    });
}

// ─────────────────────────────────────────
// UI STATES
// ─────────────────────────────────────────

function showFound(article) {
  currentArticle = article;
  document.getElementById("found-code").textContent = article.code_article;
  document.getElementById("found-name").textContent = article.designation;
  document.getElementById("state-found").classList.remove("hidden");
  document.getElementById("state-notfound").classList.add("hidden");
  setTimeout(function() {
    document.getElementById("state-found").classList.add("hidden");
    showQtyPanel(article);
  }, 600);
}

function showNotFound(barcode) {
  document.getElementById("notfound-barcode").textContent = barcode;
  document.getElementById("state-notfound").classList.remove("hidden");
  document.getElementById("state-found").classList.add("hidden");
  setTimeout(function() {
    document.getElementById("state-notfound").classList.add("hidden");
    resumeScanning();
  }, 2000);
}

function showQtyPanel(article) {
  document.getElementById("qty-code").textContent = article.code_article;
  document.getElementById("qty-name").textContent = article.designation;
  document.getElementById("qty-unite").textContent = "Unite: " + article.unite;

  var panel = document.getElementById("qty-panel");
  var warnBox = document.getElementById("qty-existing-warn");
  var input = document.getElementById("qty-input");

  // Hide warning by default
  warnBox.classList.add("hidden");
  input.value = "";

  // Check if article already scanned in this reception (only if online)
  if (navigator.onLine) {
    fetch("/api/check-ligne?article_id=" + article.id)
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.exists) {
          // Pre-fill with existing qty and show warning
          input.value = data.qte % 1 === 0 ? data.qte : data.qte.toFixed(2);
          document.getElementById("qty-existing-value").textContent = data.qte + " " + article.unite;
          warnBox.classList.remove("hidden");
          input.focus();
          input.select();
        } else {
          input.focus();
        }
      })
      .catch(function() {
        input.focus();
      });
  } else {
    input.focus();
  }

  panel.classList.add("visible");
  panel.setAttribute("aria-hidden", "false");
}

function hideQtyPanel() {
  var panel = document.getElementById("qty-panel");
  panel.classList.remove("visible");
  panel.setAttribute("aria-hidden", "true");
  currentArticle = null;
  setTimeout(function() {
    document.getElementById("manual-input").focus();
  }, 400);
}

function changeQty(delta) {
  var input = document.getElementById("qty-input");
  var val = parseFloat(input.value) || 0;
  val = Math.max(0, val + delta);
  input.value = val % 1 === 0 ? val : val.toFixed(2);
}

// ─────────────────────────────────────────
// CONFIRM ADD - WITH OFFLINE SUPPORT
// ─────────────────────────────────────────

function confirmAdd() {
  if (!currentArticle) return;
  var qteRaw = document.getElementById("qty-input").value;
  if (qteRaw === "" || qteRaw === null) {
    showToast("Entrez une quantite", "warning");
    return;
  }
  var qte = parseFloat(qteRaw);
  if (isNaN(qte) || qte < 0) {
    showToast("Quantite invalide", "warning");
    return;
  }
  var confirmBtn = document.getElementById("confirm-add-btn");
  if (confirmBtn) confirmBtn.disabled = true;
  var article = currentArticle;

  if (!navigator.onLine) {
    queueScan(article.id, qte, article)
      .then(function() {
        showToast(article.designation + " - " + qte + " " + article.unite + " (hors ligne)", "warning");
        hideQtyPanel();
        resumeScanning();
      })
      .catch(function() {
        showToast("Erreur sauvegarde locale", "error");
        resumeScanning();
      });
    if (confirmBtn) confirmBtn.disabled = false;
    return;
  }

  fetch("/api/add-ligne", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ article_id: article.id, qte: qte })
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (data.success) {
      if (data.was_existing) {
        showToast("Qte remplacee: " + data.old_qte + " → " + qte + " " + article.unite, "success");
      } else {
        showToast(article.designation + " - " + qte + " " + article.unite, "success");
      }
      var badge = document.getElementById("badge-count");
      badge.textContent = data.total_lignes;
      badge.classList.remove("hidden");
      hideQtyPanel();
      resumeScanning();
    } else {
      showToast(data.message || "Erreur", "error");
      resumeScanning();
    }
    if (confirmBtn) confirmBtn.disabled = false;
  })
  .catch(function() {
    queueScan(article.id, qte, article)
      .then(function() {
        showToast(article.designation + " sauvegarde hors ligne", "warning");
        hideQtyPanel();
        resumeScanning();
      })
      .catch(function() {
        showToast("Erreur sauvegarde", "error");
        resumeScanning();
      });
    if (confirmBtn) confirmBtn.disabled = false;
  });
}

// ─────────────────────────────────────────
// OTHER ACTIONS
// ─────────────────────────────────────────

function cancelScan() { hideQtyPanel(); resumeScanning(); }

function resumeScanning() {
  isPaused = false;
  setTimeout(function() {
    scanCooldown = false;
    document.getElementById("manual-input").focus();
  }, 500);
}

function manualSearch() {
  var input = document.getElementById("manual-search-input");
  var barcode = input.value.trim();
  if (!barcode) { showToast("Entrez un code-barres", "warning"); return; }
  input.value = "";
  processBarcode(barcode);
}

function manualLookup() {
  var input = document.getElementById("manual-input");
  var barcode = input.value.trim();
  if (!barcode) { showToast("Entrez un code-barres", "warning"); return; }
  input.value = "";
  processBarcode(barcode);
}

function finishReception() {
  if (!navigator.onLine) {
    queueFinish()
      .then(function() {
        // Mark as pending finish so home page knows
        localStorage.setItem('pmd_pending_finish', '1');
        showToast('Reception sauvegardee - sync quand connexion retablie', 'warning');
        setTimeout(function() { window.location.href = '/'; }, 1500);
      })
      .catch(function() {
        showToast('Erreur sauvegarde locale', 'error');
      });
    return;
  }

  fetch("/api/finish-reception", { method: "POST" })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (data.success) {
      localStorage.removeItem('pmd_reception_ref');
      localStorage.removeItem('pmd_reception_id');
      localStorage.removeItem('pmd_pending_finish');
      showToast("Reception sauvegardee", "success");
      setTimeout(function() { window.location.href = "/"; }, 1200);
    }
  })
  .catch(function() {
    queueFinish()
      .then(function() {
        localStorage.setItem('pmd_pending_finish', '1');
        showToast('Reception sauvegardee - sync quand connexion retablie', 'warning');
        setTimeout(function() { window.location.href = '/'; }, 1500);
      })
      .catch(function() {
        showToast('Erreur sauvegarde', 'error');
      });
  });
}

document.addEventListener("keydown", function(e) {
  if (e.key === "Enter" || e.keyCode === 13) {
    var qtyPanel = document.getElementById("qty-panel");
    if (qtyPanel && qtyPanel.classList.contains("visible")) {
      confirmAdd();
    }
  }
});