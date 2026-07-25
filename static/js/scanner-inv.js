// PMD Verification Scanner - Online only mode

var currentArticle = null;
var currentQteSysteme = 0;
var isPaused = false;
var scanCooldown = false;
var scanTimer = null;

window.addEventListener("DOMContentLoaded", function() {
  loadSessionInfo();
  setupScanner();
});

function loadSessionInfo() {
  fetch("/api/current-inventaire")
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (!data.active) {
        window.location.href = "/verify";
        return;
      }
      document.getElementById("header-ref").textContent = data.reference;
      var badge = document.getElementById("badge-count");
      if (data.total_lignes > 0) {
        badge.textContent = data.total_lignes;
        badge.classList.remove("hidden");
      }
    })
    .catch(function() {
      showToast("Erreur réseau - reconnectez-vous", "error");
    });
}

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

  // ── Hidden input handlers (main path when laser goes here)
  manualInput.addEventListener("input", function() {
    var val = manualInput.value;
    if (val.indexOf("\n") !== -1 || val.indexOf("\r") !== -1) {
      var barcode = val.replace(/[\r\n]/g, "").trim();
      manualInput.value = "";
      if (barcode.length >= 4) processBarcode(barcode);
      return;
    }
    clearTimeout(scanTimer);
    scanTimer = setTimeout(function() {
      var barcode = manualInput.value.trim();
      if (barcode.length >= 4) {
        manualInput.value = "";
        processBarcode(barcode);
      }
    }, 150);
  });

  manualInput.addEventListener("keydown", function(e) {
    if (e.key === "Enter" || e.keyCode === 13) {
      e.preventDefault();
      clearTimeout(scanTimer);
      var barcode = manualInput.value.trim();
      manualInput.value = "";
      if (barcode.length >= 4) processBarcode(barcode);
    }
  });

  // ── Manual search input handlers (fallback when laser goes here)
  manualSearchInput.addEventListener("input", function() {
    var val = manualSearchInput.value;
    if (val.indexOf("\n") !== -1 || val.indexOf("\r") !== -1) {
      var barcode = val.replace(/[\r\n]/g, "").trim();
      manualSearchInput.value = "";
      if (barcode.length >= 4) processBarcode(barcode);
      return;
    }
    clearTimeout(scanTimer);
    scanTimer = setTimeout(function() {
      var barcode = manualSearchInput.value.trim();
      // Auto-process only if long barcode (from laser scan)
      if (barcode.length >= 8) {
        manualSearchInput.value = "";
        processBarcode(barcode);
      }
    }, 150);
  });

  manualSearchInput.addEventListener("keydown", function(e) {
    if (e.key === "Enter" || e.keyCode === 13) {
      e.preventDefault();
      clearTimeout(scanTimer);
      var barcode = manualSearchInput.value.trim();
      manualSearchInput.value = "";
      if (barcode.length >= 4) processBarcode(barcode);
    }
  });
}

function processBarcode(barcode) {
  if (isPaused || scanCooldown) return;
  isPaused = true;
  scanCooldown = true;

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
      showToast("Erreur réseau", "error");
      resumeScanning();
    });
}

function showFound(article) {
  currentArticle = article;
  document.getElementById("found-code").textContent = article.code_article;
  document.getElementById("found-name").textContent = article.designation;
  document.getElementById("state-found").classList.remove("hidden");
  document.getElementById("state-notfound").classList.add("hidden");
  setTimeout(function() {
    document.getElementById("state-found").classList.add("hidden");
    fetchStockAndShowPanel(article);
  }, 400);
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

function fetchStockAndShowPanel(article) {
  // Fetch stock/price AND check if already scanned in parallel
  Promise.all([
    fetch("/api/stock-level?article_code=" + encodeURIComponent(article.code_article)).then(function(r) { return r.json(); }),
    fetch("/api/check-inventaire-ligne?article_id=" + article.id).then(function(r) { return r.json(); })
  ])
  .then(function(results) {
    var stockData = results[0];
    var checkData = results[1];
    currentQteSysteme = stockData.quantity || 0;
    showQtyPanel(article, currentQteSysteme, stockData.price, checkData);
  })
  .catch(function() {
    currentQteSysteme = 0;
    showQtyPanel(article, 0, null, {exists: false});
  });
}

function showQtyPanel(article, qteSysteme, prix, checkData) {
  document.getElementById("qty-code").textContent = article.code_article;
  document.getElementById("qty-name").textContent = article.designation;
  document.getElementById("qty-systeme").textContent = qteSysteme + " " + (article.unite || "");

  var prixEl = document.getElementById("qty-prix");
  if (prixEl) {
    if (prix !== null && prix !== undefined) {
      prixEl.textContent = parseFloat(prix).toFixed(2) + " MAD";
      prixEl.style.color = "#10B981";
      prixEl.style.fontSize = "22px";
    } else {
      prixEl.textContent = "Prix non mentionné";
      prixEl.style.color = "#8B8B8B";
      prixEl.style.fontSize = "13px";
    }
  }

  var input = document.getElementById("qty-input");
  var warnBox = document.getElementById("qty-existing-warn");

  // Rescan detection
  if (checkData && checkData.exists) {
    input.value = checkData.qte_physique % 1 === 0 ? checkData.qte_physique : checkData.qte_physique.toFixed(2);
    if (warnBox) {
      document.getElementById("qty-existing-value").textContent = checkData.qte_physique + " " + (article.unite || "");
      warnBox.classList.remove("hidden");
    }
    updateEcartPreview();
  } else {
    input.value = "";
    if (warnBox) warnBox.classList.add("hidden");
  }

  document.getElementById("qty-ecart-preview").classList.add("hidden");
  if (checkData && checkData.exists) {
    updateEcartPreview();
  }

  var panel = document.getElementById("qty-panel");
  panel.classList.add("visible");
  panel.setAttribute("aria-hidden", "false");

  setTimeout(function() {
    input.focus();
    if (checkData && checkData.exists) input.select();
  }, 300);
}

function hideQtyPanel() {
  var panel = document.getElementById("qty-panel");
  panel.classList.remove("visible");
  panel.setAttribute("aria-hidden", "true");
  currentArticle = null;
  currentQteSysteme = 0;
  setTimeout(function() {
    document.getElementById("manual-input").focus();
  }, 400);
}

function changeQty(delta) {
  var input = document.getElementById("qty-input");
  var val = parseFloat(input.value) || 0;
  val = Math.max(0, val + delta);
  input.value = val % 1 === 0 ? val : val.toFixed(2);
  updateEcartPreview();
}

function updateEcartPreview() {
  var input = document.getElementById("qty-input");
  var preview = document.getElementById("qty-ecart-preview");
  var val = parseFloat(input.value);

  if (isNaN(val) || input.value === "") {
    preview.classList.add("hidden");
    return;
  }

  var ecart = val - currentQteSysteme;
  preview.classList.remove("hidden");

  if (ecart === 0) {
    preview.style.background = "#E7F8F1";
    preview.style.color = "#059669";
    preview.style.border = "1px solid rgba(16,185,129,0.3)";
    preview.textContent = "Écart: 0 (stock correct)";
  } else if (ecart > 0) {
    preview.style.background = "#FEF9E7";
    preview.style.color = "#B45309";
    preview.style.border = "1px solid rgba(234,179,8,0.3)";
    preview.textContent = "Écart: +" + ecart + " (surplus)";
  } else {
    preview.style.background = "#FEECEC";
    preview.style.color = "#DC2626";
    preview.style.border = "1px solid rgba(239,68,68,0.3)";
    preview.textContent = "Écart: " + ecart + " (manquant)";
  }
}

function confirmAdd() {
  if (!currentArticle) return;
  var qteRaw = document.getElementById("qty-input").value;
  if (qteRaw === "" || qteRaw === null) {
    showToast("Entrez une quantité", "warning");
    return;
  }
  var qte = parseFloat(qteRaw);
  if (isNaN(qte) || qte < 0) {
    showToast("Quantité invalide", "warning");
    return;
  }

  var confirmBtn = document.getElementById("confirm-add-btn");
  if (confirmBtn) confirmBtn.disabled = true;
  var article = currentArticle;

  fetch("/api/add-inventaire-ligne", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ article_id: article.id, qte_physique: qte })
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (data.success) {
      var msg;
      if (data.was_existing) {
        msg = "Qte remplacée: " + data.old_qte_physique + " → " + qte + " - Écart: " + (data.ecart > 0 ? "+" : "") + data.ecart;
      } else {
        msg = article.designation + " - Écart: " + (data.ecart > 0 ? "+" : "") + data.ecart;
      }
      var type = data.ecart === 0 ? "success" : "warning";
      showToast(msg, type);

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
    showToast("Erreur réseau", "error");
    if (confirmBtn) confirmBtn.disabled = false;
    resumeScanning();
  });
}

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

function finishInventaire() {
  fetch("/api/finish-inventaire", { method: "POST" })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.success) {
        showToast("Inventaire sauvegardé", "success");
        setTimeout(function() { window.location.href = "/verify"; }, 1200);
      }
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