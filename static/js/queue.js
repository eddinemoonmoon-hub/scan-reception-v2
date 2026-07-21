// PMD Reception — Offline Queue & Article Cache
// Handles local article storage and pending scan queue

var DB_NAME = 'pmd-reception-db';
var DB_VERSION = 1;
var db = null;

// Open IndexedDB
function openDB() {
  return new Promise(function(resolve, reject) {
    if (db) { resolve(db); return; }
    var request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = function(e) {
      var database = e.target.result;

      // Store for all articles (local lookup)
      if (!database.objectStoreNames.contains('articles')) {
        var articleStore = database.createObjectStore('articles', { keyPath: 'id' });
        articleStore.createIndex('barcode', 'barcode', { unique: true });
        articleStore.createIndex('code_article', 'code_article', { unique: true });
      }

      // Store for pending scans (offline queue)
      if (!database.objectStoreNames.contains('pending_scans')) {
        database.createObjectStore('pending_scans', {
          keyPath: 'id',
          autoIncrement: true
        });
      }

      // Store for metadata (last sync time etc)
      if (!database.objectStoreNames.contains('meta')) {
        database.createObjectStore('meta', { keyPath: 'key' });
      }
    };

    request.onsuccess = function(e) {
      db = e.target.result;
      resolve(db);
    };

    request.onerror = function(e) {
      reject(e.target.error);
    };
  });
}

// ─────────────────────────────────────────
// ARTICLE CACHE
// ─────────────────────────────────────────

function syncArticles() {
  // Always sync when online so article changes appear immediately.
  // Important: clear local cache first so deleted/inactive articles disappear.
  if (!navigator.onLine) {
    console.log('[Queue] Offline - using existing article cache');
    return Promise.resolve();
  }

  return openDB().then(function() {
    console.log('[Queue] Syncing articles from server...');
    return fetch('/api/articles')
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (!data.success || !data.articles) {
          console.log('[Queue] Article sync failed - invalid server response');
          return;
        }

        // Clear old local article cache first, then store fresh server data.
        // This removes old inactive/deleted articles such as -2 / -3 duplicates.
        return clearArticlesCache()
          .then(function() {
            return storeArticles(data.articles);
          })
          .then(function() {
            return setMetaValue('last_article_sync', Date.now());
          })
          .then(function() {
            console.log('[Queue] Synced fresh ' + data.count + ' articles to local cache');
          });
      })
      .catch(function() {
        console.log('[Queue] Article sync failed, using existing cache');
      });
  });
}
function clearArticlesCache() {
  return openDB().then(function(database) {
    return new Promise(function(resolve, reject) {
      var tx = database.transaction('articles', 'readwrite');
      var store = tx.objectStore('articles');
      var request = store.clear();

      request.onsuccess = function() { resolve(); };
      request.onerror = function(e) { reject(e.target.error); };
    });
  });
}
function storeArticles(articles) {
  return openDB().then(function(database) {
    return new Promise(function(resolve, reject) {
      var tx = database.transaction('articles', 'readwrite');
      var store = tx.objectStore('articles');
      articles.forEach(function(a) { store.put(a); });
      tx.oncomplete = function() { resolve(); };
      tx.onerror = function(e) { reject(e.target.error); };
    });
  });
}

function localLookup(barcode) {
  return openDB().then(function(database) {
    return new Promise(function(resolve, reject) {
      var tx = database.transaction('articles', 'readonly');
      var store = tx.objectStore('articles');
      var index = store.index('barcode');
      var request = index.get(barcode);
      request.onsuccess = function(e) {
        var article = e.target.result;
        if (article) {
          resolve({ found: true, article: article });
        } else {
          resolve({ found: false });
        }
      };
      request.onerror = function(e) { reject(e.target.error); };
    });
  });
}

function getArticleCacheCount() {
  return openDB().then(function(database) {
    return new Promise(function(resolve) {
      var tx = database.transaction('articles', 'readonly');
      var store = tx.objectStore('articles');
      var request = store.count();
      request.onsuccess = function(e) { resolve(e.target.result); };
      request.onerror = function() { resolve(0); };
    });
  });
}

// ─────────────────────────────────────────
// PENDING SCAN QUEUE
// ─────────────────────────────────────────

function queueScan(article_id, qte, article) {
  return openDB().then(function(database) {
    return new Promise(function(resolve, reject) {
      var tx = database.transaction('pending_scans', 'readwrite');
      var store = tx.objectStore('pending_scans');
      var scan = {
        type: 'scan',
        article_id: article_id,
        qte: qte,
        article_designation: article.designation,
        article_code: article.code_article,
        article_unite: article.unite,
        timestamp: Date.now()
      };
      var request = store.add(scan);
      request.onsuccess = function() { resolve(); };
      request.onerror = function(e) { reject(e.target.error); };
    });
  });
}

function queueFinish() {
  return openDB().then(function(database) {
    return new Promise(function(resolve, reject) {
      var tx = database.transaction('pending_scans', 'readwrite');
      var store = tx.objectStore('pending_scans');
      var item = {
        type: 'finish',
        timestamp: Date.now()
      };
      var request = store.add(item);
      request.onsuccess = function() { resolve(); };
      request.onerror = function(e) { reject(e.target.error); };
    });
  });
}

function getPendingScans() {
  return openDB().then(function(database) {
    return new Promise(function(resolve, reject) {
      var tx = database.transaction('pending_scans', 'readonly');
      var store = tx.objectStore('pending_scans');
      var request = store.getAll();
      request.onsuccess = function(e) { resolve(e.target.result); };
      request.onerror = function(e) { reject(e.target.error); };
    });
  });
}

function removePendingScan(id) {
  return openDB().then(function(database) {
    return new Promise(function(resolve, reject) {
      var tx = database.transaction('pending_scans', 'readwrite');
      var store = tx.objectStore('pending_scans');
      var request = store.delete(id);
      request.onsuccess = function() { resolve(); };
      request.onerror = function(e) { reject(e.target.error); };
    });
  });
}

function getPendingCount() {
  return openDB().then(function(database) {
    return new Promise(function(resolve) {
      var tx = database.transaction('pending_scans', 'readonly');
      var store = tx.objectStore('pending_scans');
      var request = store.count();
      request.onsuccess = function(e) { resolve(e.target.result); };
      request.onerror = function() { resolve(0); };
    });
  });
}

function drainQueue() {
  return getPendingScans().then(function(items) {
    if (items.length === 0) return;
    console.log('[Queue] Draining ' + items.length + ' pending items...');

    var chain = Promise.resolve();
    var synced = 0;
    var failed = 0;
    var finished = false;

    items.forEach(function(item) {
      chain = chain.then(function() {

        // Handle finish reception item
        if (item.type === 'finish') {
          return fetch('/api/finish-reception', { method: 'POST' })
            .then(function(r) { return r.json(); })
            .then(function(data) {
              if (data.success) {
                finished = true;
                localStorage.removeItem('pmd_reception_ref');
                localStorage.removeItem('pmd_reception_id');
                return removePendingScan(item.id);
              }
            })
            .catch(function() {
              failed++;
            });
        }

        // Handle scan item
        return fetch('/api/add-ligne', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            article_id: item.article_id,
            qte: item.qte
          })
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
          if (data.success) {
            synced++;
            return removePendingScan(item.id).then(function() {
              var badge = document.getElementById('badge-count');
              if (badge && data.total_lignes > 0) {
                badge.textContent = data.total_lignes;
                badge.classList.remove('hidden');
              }
            });
          } else {
            failed++;
          }
        })
        .catch(function() {
          failed++;
        });

      });
    });

    return chain.then(function() {
      if (synced > 0) {
        showToast(synced + ' scan(s) synchronise(s)', 'success');
      }
      if (failed > 0) {
        showToast(failed + ' element(s) non synchronise(s)', 'error');
      }
      if (finished) {
        showToast('Reception terminee et synchronisee', 'success');
        setTimeout(function() { window.location.href = '/'; }, 1500);
      }
    });
  });
}

// ─────────────────────────────────────────
// META STORE HELPERS
// ─────────────────────────────────────────

function getMetaValue(key) {
  return openDB().then(function(database) {
    return new Promise(function(resolve) {
      var tx = database.transaction('meta', 'readonly');
      var store = tx.objectStore('meta');
      var request = store.get(key);
      request.onsuccess = function(e) {
        resolve(e.target.result ? e.target.result.value : null);
      };
      request.onerror = function() { resolve(null); };
    });
  });
}

function setMetaValue(key, value) {
  return openDB().then(function(database) {
    return new Promise(function(resolve, reject) {
      var tx = database.transaction('meta', 'readwrite');
      var store = tx.objectStore('meta');
      var request = store.put({ key: key, value: value });
      request.onsuccess = function() { resolve(); };
      request.onerror = function(e) { reject(e.target.error); };
    });
  });
}