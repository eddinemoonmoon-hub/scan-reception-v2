// PMD Économat Scanner JS - Online mode

var currentArticle = null;
var currentStockEconomat = 0;
var currentDocType = 'entree';
var isPaused = false;
var scanCooldown = false;
var scanTimer = null;

window.addEventListener("DOMContentLoaded", function() {
  loadSessionInfo();
  setupScanner();
});

function loadSessionInfo() {
  fetch("/api/economat/current")
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (!data.active) {
        window.location.href = "/";
        return;
      }
      currentDocType = data.type;
      var title = currentDocType === 'entree' ? 'Économat - Entrée' : 'Économat - Sortie';
      document.getElementById("header-title").textContent = title;
      document.getElementById("header-ref").textContent = data.reference + " (" + data.agent_name + ")";

      // Style badge
      var typeBadge = document.getElementById("header-type-badge");
      if (typeBadge) {
        typeBadge.textContent = currentDocType.toUpperCase();
        typeBadge.style.background = currentDocType === 'entree' ? '#E7F8F1' : '#FEECEC';
        typeBadge.style.color = currentDocType === 'entree' ? '#059669' : '#DC2626';
      }

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
    fetchEconomatStockAndShowPanel(article);
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

function fetchEconomatStockAndShowPanel(article) {
  Promise.all([
    fetch("/api/economat/stock?article_id=" + article.id).then(function(r) { return r.json(); }),
    fetch("/api/economat/check-ligne?article_id=" + article.id).then(function(r) { return r.json(); })
  ])
  .then(function(results) {
    var stockData = results[0];
    var checkData = results[1];
    currentStockEconomat = stockData.qte || 0;
    showQtyPanel(article, currentStockEconomat, checkData);
  })
  .catch(function() {
    currentStockEconomat = 0;
    showQtyPanel(article, 0, {exists: false});
  });
}

function showQtyPanel(article, stockEconomat, checkData) {
  document.getElementById("qty-code").textContent = article.code_article;
  document.getElementById("qty-name").textContent = article.designation;
  document.getElementById("qty-stock-eco").textContent = stockEconomat + " " + (article.unite || "");

  var input = document.getElementById("qty-input");
  var warnBox = document.getElementById("qty-existing-warn");

  if (checkData && checkData.exists) {
    input.value = checkData.qte % 1 === 0 ? checkData.qte : checkData.qte.toFixed(2);
    if (warnBox) {
      document.getElementById("qty-existing-value").textContent = checkData.qte + " " + (article.unite || "");
      warnBox.classList.remove("hidden");
    }
  } else {
    input.value = "";
    if (warnBox) warnBox.classList.add("hidden");
  }

  // Set button text according to type
  var btnText = document.getElementById("confirm-btn-text");
  if (btnText) {
    btnText.textContent = currentDocType === 'entree' ? 'Ajouter au stock' : 'Retirer du stock';
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
  currentStockEconomat = 0;
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

function confirmAdd() {
  if (!currentArticle) return;
  var qteRaw = document.getElementById("qty-input").value;
  if (qteRaw === "" || qteRaw === null) {
    showToast("Entrez une quantité", "warning");
    return;
  }
  var qte = parseFloat(qteRaw);
  if (isNaN(qte) || qte <= 0) {
    showToast("Quantité invalide", "warning");
    return;
  }

  var confirmBtn = document.getElementById("confirm-add-btn");
  if (confirmBtn) confirmBtn.disabled = true;
  var article = currentArticle;

  fetch("/api/economat/add-ligne", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ article_id: article.id, qte: qte })
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (data.success) {
      var msg = (currentDocType === 'entree' ? '+ ' : '- ') + qte + ' ' + article.unite + ' (' + article.designation + ')';
      showToast(msg, 'success');

      var badge = document.getElementById("badge-count");
      badge.textContent = data.total_lignes;
      badge.classList.remove("hidden");

      hideQtyPanel();
      resumeScanning();
    } else {
      showToast(data.message || "Erreur", "error");
      if (confirmBtn) confirmBtn.disabled = false;
      // Don't hide panel if stock insufficient
      if (data.message && data.message.indexOf("insuffisant") !== -1) {
        document.getElementById("qty-input").focus();
      } else {
        resumeScanning();
      }
    }
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

function finishDocument() {
  fetch("/api/economat/finish", { method: "POST" })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.success) {
        showToast("Document " + data.reference + " validé", "success");
        setTimeout(function() { window.location.href = "/"; }, 1200);
      } else {
        showToast(data.message || "Erreur", "error");
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