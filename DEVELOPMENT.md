# Development Changelog - Scan Reception Project

## Overview
This document summarizes the key issues faced during development and the solutions implemented to create a responsive, fast, and premium mobile-first barcode scanning application for reception workflows.

---

## Issues and Solutions

### 1. Mobile Scanner Camera Behavior & HTTPS Access
**Problem:** 
- Scanner failed to start on mobile due to `getUserMedia` being undefined.
- Local HTTPS access required for camera permissions on mobile browsers.
- Initial implementation used adhoc SSL but lacked proper certificate handling.

**Solution:**
- Enhanced `app.py` with environment-variable-driven SSL context loader (`get_ssl_context()`).
- Added support for custom `SSL_CERT_PATH` and `SSL_KEY_PATH` environment variables.
- Fallback to adhoc SSL for development.
- Improved startup logging to show which addresses are being served.

**Files changed:**
- `app.py`

### 2. Broken Scanner Library (Instascan) and Performance
**Problem:**
- Original scanner relied on Instascan CDN which was unreliable/undefined.
- Scanning performance was laggy, especially on mobile.
- No back-camera preference; often used front-facing camera by default.

**Solution:**
- Replaced Instascan with ZXing (`@zxing/library`) via CDN.
- Added dynamic script loading with proper error handling.
- Implemented back/rear camera selection logic (prefers "back", "rear", or "environment" facing cameras).
- Added camera resolution constraints (ideal 640×480) to reduce processing load.
- Added `facingMode: environment` hint for better camera selection on mobile.

**Files changed:**
- `static/js/scanner.js`

### 3. Native BarcodeDetector Integration (Performance Boost)
**Problem:**
- ZXing decoding, while functional, was not instant enough for a smooth user experience on mid-tier mobile devices.

**Solution:**
- Added a fast-path using the native `BarcodeDetector` API (available in Chrome/Brave on Android).
- When supported, the app uses `BarcodeDetector` with a lightweight frame loop:
  - Captures video at 640×480 ideal.
  - Uses `createImageBitmap` to downscale to 320×240 for detection.
  - Detects common 1D formats (EAN, UPC, Code 128, etc.).
  - Pauses briefly after a read to avoid duplicates.
- Falls back to ZXing if the native API is unavailable or unsupported.
- This change resulted in near-instant barcode detection on supported devices.

**Files changed:**
- `static/js/scanner.js`

### 4. Mobile-First Premium UI Redesign (Green Theme)
**Problem:**
- The original UI felt generic and not optimized for mobile use.
- Buttons and panels were not sufficiently tappable.
- Lacked a premium, cohesive look.

**Solution:**
- Complete redesign of `static/css/app.css` with a fresh green premium theme:
  - Color palette: `--primary: #62d58b`, `--green: #62d58b`, `--green2: #30c27b`, dark background (`#041012`).
  - Added responsive gradients, depth with shadows and overlays.
  - Updated header, bottom nav, buttons, form inputs, and toast messages.
  - Made the scan overlay and frame more visually distinct with animated scan line.
  - Improved touch targets (minimum 48px for buttons).
  - Used CSS transforms for animations (GPU-accelerated) to avoid layout thrash.

**Files changed:**
- `static/css/app.css`

### 5. Responsive Quantity Input Panel
**Problem:**
- The quantity panel appeared abruptly and was not optimized for mobile keyboards.
- Buttons were small and not ideal for touch.

**Solution:**
- Made the quantity panel fixed to the bottom with safe-area insets.
- Animated panel entrance/exit using CSS transforms (`translateY`) for smoothness.
- Increased button sizes (48x48px) and made confirm button full-width on small screens.
- Added `inputmode="numeric"` and `pattern="[0-9]*"` to the quantity input for optimal mobile keyboard.
- Added ARIA labels for accessibility.
- Delayed focus on quantity input to ensure mobile keyboard opens reliably.
- Disabled confirm button during API requests to prevent double submits.

**Files changed:**
- `templates/reception/scan.html`
- `static/js/scanner.js`
- `static/css/app.css`

### 6. Performance and Responsiveness Tweaks
**Problem:**
- Debug messages were causing layout thrash on mobile due to frequent DOM updates.
- Scan cooldowns felt too long, making the app seem unresponsive.
- Camera start/stop logic could be improved for rapid toggling.

**Solution:**
- Throttled debug DOM updates to every 300ms.
- Reduced scan cooldown from 1500ms to 800ms for snappier resumption.
- Improved camera start/stop with proper cleanup of `codeReader` and media streams.
- Used `requestAnimationFrame` for the BarcodeDetector loop to align with display refresh.
- Added `will-change` hints for animated elements.

**Files changed:**
- `static/js/scanner.js`
- `static/css/app.css`

---

## Files Modified Summary

- `app.py` – SSL context and Flask serving improvements.
- `templates/reception/scan.html` – Structural updates for mobile inputs, ARIA, and panel visibility.
- `static/js/scanner.js` – Complete rewrite to support BarcodeDetector, ZXing fallback, camera constraints, performance tweaks, and UI integration.
- `static/css/app.css` – Premium green theme, responsive layout, animated elements, and mobile-first controls.

---

## Next Steps / Future Improvements

1. **Bundle ZXing Locally** – To eliminate CDN latency and enable offline use.
2. **Web Worker for Detection** – Offload barcode decoding (ZXing path) to a worker to keep UI thread free.
3. **Haptic Feedback** – Add subtle vibrations on successful scan using Vibration API.
4. **Scan Sound** – Play a short beep on successful detection (with user toggle).
5. **Advanced Camera Controls** – Expose torch/flashlight toggle in UI.
6. **Offline Fallback Queue** – Queue scans when offline and sync on reconnect.
7. **End-to-End Tests** – Add Cypress or Playwright tests for critical paths.
8. **Dark/Light Theme Toggle** – Allow user to switch themes via preference.

---

## Verification
All changes were tested on:
- Desktop Chrome/Firefox (localhost and HTTPS via adhoc).
- Android Chrome and Brave (HTTPS via LAN IP).
- Verified back-camera selection, instant detection (BarcodeDetector path), responsive UI, and smooth animations.

---

*Last updated: May 27, 2026*

////////////

@"
# Development Changelog - Scan Reception Project

## Overview
This document summarizes the key issues faced during development and the solutions implemented to create a responsive, fast, and premium mobile-first barcode scanning application for reception workflows.

---

## Issues and Solutions

### 1. Mobile Scanner Camera Behavior & HTTPS Access
**Problem:**
- Scanner failed to start on mobile due to getUserMedia being undefined.
- Local HTTPS access required for camera permissions on mobile browsers.
- Initial implementation used adhoc SSL but lacked proper certificate handling.

**Solution:**
- Enhanced app.py with environment-variable-driven SSL context loader.
- Added support for custom SSL_CERT_PATH and SSL_KEY_PATH environment variables.
- Fallback to adhoc SSL for development only.
- Improved startup logging to show which addresses are being served.

**Files changed:**
- app.py

---

### 2. Broken Scanner Library (Instascan) and Performance
**Problem:**
- Original scanner relied on Instascan CDN which was unreliable.
- Scanning performance was laggy, especially on mobile.
- No back-camera preference; often used front-facing camera by default.

**Solution:**
- Replaced Instascan with ZXing (@zxing/library) via CDN.
- Added dynamic script loading with proper error handling.
- Implemented back/rear camera selection logic.
- Added camera resolution constraints (ideal 640x480).
- Added facingMode: environment hint for mobile.

**Files changed:**
- static/js/scanner.js

---

### 3. Native BarcodeDetector Integration (Performance Boost)
**Problem:**
- ZXing decoding was not instant enough for smooth UX on mid-tier mobile devices.

**Solution:**
- Added fast-path using the native BarcodeDetector API (Chrome/Brave on Android).
- Captures video at 640x480, downscales to 320x240 for detection.
- Detects EAN, UPC, Code 128 and other common 1D formats.
- Falls back to ZXing if native API is unavailable.
- Near-instant barcode detection on supported devices.

**Files changed:**
- static/js/scanner.js

---

### 4. Mobile-First Premium UI Redesign (Green Theme)
**Problem:**
- Original UI felt generic and not optimized for mobile.
- Buttons and panels were not sufficiently tappable.
- Lacked a premium cohesive look.

**Solution:**
- Complete redesign of static/css/app.css with green premium theme.
- Color palette: --primary #62d58b, dark background #041012.
- Responsive gradients, depth with shadows and overlays.
- Animated scan line and visually distinct scan frame.
- Minimum 48px touch targets for all buttons.
- GPU-accelerated CSS transform animations.

**Files changed:**
- static/css/app.css

---

### 5. Responsive Quantity Input Panel
**Problem:**
- Quantity panel appeared abruptly and was not optimized for mobile keyboards.
- Buttons were small and not ideal for touch.

**Solution:**
- Fixed panel to bottom with safe-area insets.
- Animated entrance/exit using CSS translateY transforms.
- Increased button sizes to 48x48px.
- Added inputmode=numeric and pattern=[0-9]* for optimal mobile keyboard.
- Added ARIA labels for accessibility.
- Disabled confirm button during API requests to prevent double submits.

**Files changed:**
- templates/reception/scan.html
- static/js/scanner.js
- static/css/app.css

---

### 6. Performance and Responsiveness Tweaks
**Problem:**
- Debug messages causing layout thrash on mobile.
- Scan cooldowns felt too long.
- Camera start/stop logic needed improvement.

**Solution:**
- Throttled debug DOM updates to every 300ms.
- Reduced scan cooldown from 1500ms to 800ms.
- Improved camera cleanup with proper stream track stopping.
- Used requestAnimationFrame for BarcodeDetector loop.
- Added will-change hints for animated elements.

**Files changed:**
- static/js/scanner.js
- static/css/app.css

---

### 7. Production Deployment on Railway
**Problem:**
- App used adhoc SSL and app.run() directly, which crashes on production servers.
- Database (reception.db) was being tracked in Git.
- gunicorn was missing from requirements.
- No Procfile for Railway to know how to start the app.

**Solution:**
- Rewrote app.py to only use SSL locally (via environment variable flags).
- SSL is handled by Railway automatically in production (HTTPS via their proxy).
- Added .gitignore to exclude *.db, venv/, __pycache__, .env.
- Removed reception.db from Git tracking using git rm --cached.
- Added gunicorn==21.2.0 to requirements.txt.
- Created Procfile with: web: gunicorn app:app
- Deployed successfully to Railway.
- App is live at: https://scan-reception-production.up.railway.app

**Files changed:**
- app.py
- requirements.txt
- Procfile (created)
- .gitignore (created)

---

## Known Issues / Next Fixes

1. iOS Safari camera support - needs investigation and fixes.
2. PWA install button not appearing on all devices.
3. CSV import column validation too strict - barcode is the core required field.
4. Android install prompt (Add to Home Screen) needs proper manifest tuning.

---

## Files Modified Summary

- app.py - SSL context, production-ready serving, no adhoc SSL on Railway.
- templates/reception/scan.html - Mobile inputs, ARIA, panel visibility.
- static/js/scanner.js - BarcodeDetector, ZXing fallback, camera constraints, performance.
- static/css/app.css - Premium green theme, responsive layout, animations.
- requirements.txt - Added gunicorn.
- Procfile - Created for Railway deployment.
- .gitignore - Created to exclude DB, venv, cache, env files.
- DEVELOPMENT.md - This file, updated continuously.

---

## Future Improvements

1. Bundle ZXing locally to eliminate CDN latency and enable offline use.
2. Web Worker for ZXing decoding to keep UI thread free.
3. Haptic feedback on successful scan using Vibration API.
4. Scan sound - short beep on detection with user toggle.
5. Torch/flashlight toggle in scan UI.
6. Offline fallback queue - sync scans on reconnect.
7. End-to-end tests with Cypress or Playwright.
8. Dark/Light theme toggle.

---

## Verification
Tested on:
- Desktop Chrome and Firefox (localhost HTTPS via adhoc).
- Android Chrome and Brave (HTTPS via LAN IP and Railway production URL).
- Railway production deployment verified live and functional.
- Camera permission popup confirmed working on Android and Desktop.

---

*Last updated: May 27, 2026*
"@ | Out-File -FilePath "DEVELOPMENT.md" -Encoding utf8



----------------


Run this:

```powershell
@"
# Development Changelog - Scan Reception Project (PMD Reception)

## Overview
PMD Reception is a mobile-first Progressive Web App (PWA) for barcode scanning during product reception workflows. Built with Flask, SQLAlchemy, and vanilla JavaScript. Deployed on Railway with PostgreSQL.

---

## Project Structure

scan-reception/
├── app.py                  # Flask app factory, blueprints, error handlers
├── config.py               # Config class, DATABASE_URL, SECRET_KEY
├── extensions.py           # db and login_manager instances
├── requirements.txt        # Python dependencies
├── Procfile                # Gunicorn start command for Railway
├── .gitignore              # Excludes venv, db, pycache, .env
├── DEVELOPMENT.md          # This file
├── models/
│   ├── article.py          # Article model (code_article, barcode, designation, unite)
│   ├── fournisseur.py      # Fournisseur model
│   ├── reception.py        # Reception and ReceptionLigne models
│   └── user.py             # User model with password hashing
├── routes/
│   ├── admin.py            # Admin panel: articles, fournisseurs, receptions, import, export
│   ├── api.py              # JSON API: lookup, add-ligne, finish-reception, current-reception
│   ├── main.py             # Homepage and reception start
│   └── scan.py             # Scanner page route
├── static/
│   ├── css/app.css         # Full mobile-first premium green theme
│   ├── js/app.js           # Toast, PWA install button logic
│   ├── js/scanner.js       # Camera, BarcodeDetector, ZXing fallback, scan loop
│   ├── js/vendor/          # Locally bundled ZXing library
│   ├── manifest.json       # PWA manifest
│   ├── sw.js               # Service worker
│   └── icons/              # icon-192.png, icon-512.png
└── templates/
    ├── base.html           # Base layout, PWA meta tags, toast, install button
    ├── reception/
    │   ├── index.html      # Start reception page
    │   ├── scan.html       # Scanner page with qty panel
    │   └── log.html        # Reception log
    └── admin/
        ├── login.html
        ├── dashboard.html
        ├── articles/
        │   ├── list.html   # Paginated article list with search
        │   ├── form.html   # Create/edit article
        │   └── import.html # CSV/XLSX import
        ├── fournisseurs/
        │   ├── list.html
        │   └── form.html
        └── receptions/
            ├── list.html
            └── detail.html

---

## Issues and Solutions

### 1. Camera Not Working - getUserMedia Undefined
**Problem:**
- Scanner showed: Cannot read properties of undefined reading getUserMedia
- getUserMedia only works on HTTPS or localhost
- Accessing via LAN IP on HTTP blocked camera API

**Solution:**
- Added navigator.mediaDevices check before calling getUserMedia
- Added SSL support to Flask via pyopenssl and adhoc context for local dev
- Added Permissions-Policy header: camera=*, microphone=*
- Production uses Railway HTTPS proxy - no SSL needed in app

**Files:** app.py, static/js/scanner.js

---

### 2. Scanner Library Issues and Performance
**Problem:**
- Instascan CDN was unreliable and undefined on load
- ZXing decodeFromCanvas was not a function
- Quagga was laggy and caused black screen on mobile
- Scanner too slow for mid-tier Android devices

**Solution:**
- Replaced Instascan with ZXing BrowserMultiFormatReader
- Added native BarcodeDetector API as fast-path (Chrome/Brave Android)
- BarcodeDetector uses createImageBitmap downscaled to 320x240
- Falls back to ZXing when BarcodeDetector not supported
- Used requestAnimationFrame for scan loop aligned to display refresh
- Set facingMode: environment for rear camera
- Reduced resolution constraints to 640x480 to reduce processing load
- ZXing bundled locally in static/js/vendor to avoid CDN latency

**Files:** static/js/scanner.js

---

### 3. Mobile UI - Qty Panel Not Responsive
**Problem:**
- Qty input panel appeared abruptly with no animation
- Input field was cut off on the right side on mobile
- Plus and minus buttons were too small for touch
- Number input showed native browser spinners overlapping layout
- Two conflicting .qty-panel CSS definitions causing override issues

**Solution:**
- Set qty-panel to position fixed, left 0, right 0, bottom 0
- Added transform translateY(100%) hidden state and translateY(0) visible state
- Smooth animation via cubic-bezier transition
- Removed duplicate CSS block that was overriding fixed positioning
- Added min-width: 0 to qty-input for proper flex shrinking
- Removed native number spinners via webkit-appearance: none
- Added appearance: textfield for Firefox
- Minimum 52px touch targets on qty buttons
- Added inputmode=numeric and pattern=[0-9]* for mobile keyboard

**Files:** static/css/app.css, templates/reception/scan.html, static/js/scanner.js

---

### 4. Premium Mobile-First UI Redesign
**Problem:**
- Original UI was generic and not optimized for mobile warehouse use
- No cohesive theme or branding

**Solution:**
- Full redesign with green premium theme
- Color palette: --primary #62d58b, --green2 #30c27b, dark bg #041012
- GPU-accelerated animations using CSS transforms only
- Minimum 48px touch targets throughout
- Safe-area insets for iPhone notch and home bar
- Animated scan line using keyframes
- Scan frame with corner markers
- Flash effect on barcode detection
- Bottom navigation with active state indicators
- Toast notification system with icons per type

**Files:** static/css/app.css

---

### 5. PWA Install Button
**Problem:**
- No install prompt appeared for users
- beforeinstallprompt event was not being captured

**Solution:**
- Added beforeinstallprompt event listener in app.js
- Stored deferred prompt and showed custom install button
- Install button fixed bottom-right, green gradient, hidden by default
- Shows automatically when browser fires beforeinstallprompt
- Hides after install via appinstalled event
- Works on Android Chrome and desktop Chrome

**Files:** static/js/app.js, templates/base.html, static/css/app.css

---

### 6. Production Deployment on Railway
**Problem:**
- app.run with adhoc SSL crashed on Railway
- SQLite database reset on every redeploy (ephemeral filesystem)
- psycopg2-binary failed with libpq.so.5 not found on Python 3.13
- pg8000 worked but was too slow for bulk imports (timeout)
- gunicorn default 30s timeout too short for large imports
- No Procfile, no gitignore, db was tracked in Git

**Solution:**
- Removed SSL from production path, only used locally via FLASK_DEBUG flag
- Added .gitignore to exclude *.db, venv, pycache, .env
- Removed reception.db from Git tracking via git rm --cached
- Added PostgreSQL service on Railway
- Used pg8000 pure Python driver (psycopg2-binary incompatible with Railway Python 3.13)
- Set DATABASE_URL environment variable in Railway service variables
- config.py reads DATABASE_URL and replaces postgresql:// with postgresql+pg8000://
- Added Procfile: web: gunicorn app:app --timeout 300 --workers 1 --threads 4
- Added gunicorn==21.2.0 and pg8000==1.30.3 to requirements.txt

**Files:** app.py, config.py, requirements.txt, Procfile, .gitignore

---

### 7. CSV Import Issues
**Problem:**
- Import required code_article and designation but not barcode
- Barcode is the core field of the entire app
- Import failed with utf-8 codec error on files saved in other encodings
- Importing 7782 articles timed out due to one-by-one DB queries

**Solution:**
- Made barcode required alongside code_article and designation
- unite is now optional and defaults to piece
- Added multi-encoding fallback: utf-8-sig, utf-8, latin-1, cp1252
- Replaced row-by-row queries with bulk fetch then bulk_save_objects
- Pre-loads all existing codes and barcodes into memory dicts
- Single db.session.commit at end of import
- Import of 7782 articles now completes within timeout

**Files:** routes/admin.py, templates/admin/articles/import.html

---

### 8. Articles List - Pagination
**Problem:**
- All 7782 articles rendered at once caused browser to hang
- No pagination existed

**Solution:**
- Added Flask-SQLAlchemy paginate with 50 items per page
- Search query preserved across pages via URL parameter
- Page info shown: X articles - page N/M
- Precedent and Suivant navigation buttons

**Files:** routes/admin.py, templates/admin/articles/list.html

---

## Rules - What NOT To Do

1. Never push *.db files to Git - always in .gitignore
2. Never use app.run with ssl_context=adhoc in production
3. Never use psycopg2-binary on Railway Python 3.13 - use pg8000
4. Never load all records without pagination on large tables
5. Never do row-by-row DB queries in import loops - always bulk fetch
6. Never use Instascan - CDN is dead
7. Never use Quagga for mobile - too heavy and causes black screen
8. Never define the same CSS class twice - always remove the old one first
9. Never use position fixed without left, right, bottom explicitly set
10. Never skip min-width: 0 on flex children that contain inputs
11. Never commit without checking git status first
12. Never change working features without understanding why they worked

---

## Tech Stack

- Backend: Python 3.13, Flask 3.0, Flask-SQLAlchemy, Flask-Login
- Database: PostgreSQL via pg8000 driver on Railway
- Frontend: Vanilla JS, CSS custom properties, no frameworks
- Scanner: Native BarcodeDetector API with ZXing fallback
- PWA: manifest.json, service worker, beforeinstallprompt
- Deployment: Railway with gunicorn, PostgreSQL addon
- Local dev: SQLite fallback, adhoc SSL via pyopenssl

---

## Production URLs

- App: https://scan-reception-production.up.railway.app
- Admin: https://scan-reception-production.up.railway.app/admin
- Scanner: https://scan-reception-production.up.railway.app/scan

---

## Verified Working On

- Android Chrome - camera, scanner, PWA install, bulk import
- Desktop Chrome - admin panel, import, pagination
- Railway production - PostgreSQL, persistent data, HTTPS

---

## Known Remaining Issues

- iOS Safari camera support not yet tested and likely needs fixes
- PWA install not available on iOS (Apple limitation - use Add to Home Screen manually)

---

## Next Steps

1. Test and fix iOS Safari camera
2. Add torch flashlight toggle for warehouse dark environments
3. Add haptic feedback on successful scan via Vibration API
4. Add scan beep sound with user toggle
5. Offline scan queue with sync on reconnect
6. Web Worker for ZXing decoding to free UI thread

---

*Last updated: May 28, 2026*
"@ | Out-File -FilePath "DEVELOPMENT.md" -Encoding utf8
```

Then:

```powershell
git add .
git commit -m "Docs: full DEVELOPMENT.md rewrite with all issues, solutions, rules"
git push
```

Paste the output.


@"
# Development Changelog - Scan Reception Project (PMD Reception)

## Overview
PMD Reception is a mobile-first Progressive Web App (PWA) for barcode scanning during product reception workflows. Built with Flask, SQLAlchemy, and vanilla JavaScript. Deployed on Railway with PostgreSQL. Designed with Duolingo + Apple Health inspired UI.

---

## Project Structure

scan-reception/
├── app.py                  # Flask app factory, blueprints, error handlers
├── config.py               # Config class, DATABASE_URL, SECRET_KEY
├── extensions.py           # db and login_manager instances
├── requirements.txt        # Python dependencies
├── Procfile                # Gunicorn start command for Railway
├── .gitignore              # Excludes venv, db, pycache, .env
├── DEVELOPMENT.md          # This file
├── models/
│   ├── article.py          # Article model (code_article, barcode, designation, unite)
│   ├── fournisseur.py      # Fournisseur model
│   ├── reception.py        # Reception and ReceptionLigne models
│   └── user.py             # User model with password hashing
├── routes/
│   ├── admin.py            # Admin panel: articles, fournisseurs, receptions, import, export
│   ├── api.py              # JSON API: lookup, add-ligne, finish-reception, current-reception
│   ├── main.py             # Homepage and reception start
│   └── scan.py             # Scanner page route
├── static/
│   ├── css/app.css         # Duolingo + Apple Health premium theme
│   ├── js/app.js           # Toast, PWA install button logic
│   ├── js/scanner.js       # Camera, BarcodeDetector, ZXing fallback, iOS support
│   ├── js/vendor/          # Locally bundled ZXing library
│   ├── manifest.json       # PWA manifest
│   ├── sw.js               # Service worker
│   └── icons/              # icon-192.png, icon-512.png
└── templates/
    ├── base.html           # Base layout, PWA meta tags, toast, install button
    ├── reception/
    │   ├── index.html      # Start reception page
    │   ├── scan.html       # Scanner page with qty panel
    │   └── log.html        # Reception log
    └── admin/
        ├── login.html
        ├── dashboard.html
        ├── articles/
        │   ├── list.html   # Paginated article list with search
        │   ├── form.html   # Create/edit article
        │   └── import.html # CSV/XLSX import
        ├── fournisseurs/
        │   ├── list.html
        │   └── form.html
        └── receptions/
            ├── list.html
            └── detail.html

---

## Issues and Solutions (Chronological)

### 1. Camera Not Working - getUserMedia Undefined
**Problem:** Scanner showed Cannot read properties of undefined reading getUserMedia. getUserMedia only works on HTTPS or localhost. Accessing via LAN IP on HTTP blocked camera API.

**Solution:** Added navigator.mediaDevices check before calling getUserMedia. Added SSL support via pyopenssl and adhoc context for local dev. Added Permissions-Policy header. Production uses Railway HTTPS proxy.

**Files:** app.py, static/js/scanner.js

---

### 2. Scanner Library Evolution
**Problem:** Instascan CDN was dead. ZXing decodeFromCanvas was not a function. Quagga caused black screen and lag on mobile.

**Solution:** Final architecture uses three paths:
- Path 1: Native BarcodeDetector API (Android Chrome/Brave) - near instant
- Path 2: ZXing BrowserMultiFormatReader via local bundle
- Path 3: ZXing CDN fallback
BarcodeDetector uses createImageBitmap downscaled to 320x240. requestAnimationFrame for scan loop. facingMode environment for rear camera. Resolution 640x480 to reduce load.

**Files:** static/js/scanner.js, static/js/vendor/index.min.js

---

### 3. iOS Safari Camera Support
**Problem:** getVideoInputDevices() fails on iOS before permission granted. decodeFromConstraints unreliable on iOS. iOS requires playsinline attribute.

**Solution:** iOS detection via user agent. On iOS: call getUserMedia first with facingMode only to get permission, then enumerate devices, then pick back camera, then start ZXing. Added playsinline attribute to video element. Skip BarcodeDetector on iOS (not supported in Safari).

**Files:** static/js/scanner.js, templates/reception/scan.html

---

### 4. Qty Panel Not Responsive
**Problem:** Two conflicting .qty-panel CSS definitions. Input field cut off on right side on mobile. Native number spinners overlapping layout.

**Solution:** Removed duplicate CSS block. Set position fixed with left/right/bottom 0. Added min-width 0 for flex shrinking. Removed native spinners via webkit-appearance none. 56px touch targets on qty buttons. inputmode numeric for mobile keyboard.

**Files:** static/css/app.css

---

### 5. Production Deployment on Railway
**Problem:** app.run with adhoc SSL crashed. SQLite reset on every redeploy. psycopg2-binary failed with libpq.so.5 not found on Python 3.13.

**Solution:** Removed SSL from production path. Added PostgreSQL on Railway. Used pg8000 pure Python driver. config.py reads DATABASE_URL and replaces postgresql:// with postgresql+pg8000://. Procfile: gunicorn app:app --timeout 300 --workers 1 --threads 4. gitignore excludes db, venv, pycache, env.

**Files:** app.py, config.py, requirements.txt, Procfile, .gitignore

---

### 6. CSV Import Issues
**Problem:** barcode was not required on import. UTF-8 codec error on non-UTF8 files. 7782 article import timed out due to row-by-row queries.

**Solution:** Made barcode required alongside code_article and designation. Multi-encoding fallback: utf-8-sig, utf-8, latin-1, cp1252. Bulk fetch existing articles into memory dicts then bulk_save_objects. Single commit at end.

**Files:** routes/admin.py, templates/admin/articles/import.html

---

### 7. Articles List Pagination
**Problem:** 7782 articles rendered at once caused browser hang.

**Solution:** Flask-SQLAlchemy paginate with 50 items per page. Search preserved across pages. Precedent/Suivant navigation.

**Files:** routes/admin.py, templates/admin/articles/list.html

---

### 8. Export Format
**Problem:** Export included headers and many columns. Target format is barcode;qte only, no header, CP1252 encoding.

**Solution:** Raw export with no header. Format: barcode;qte per line. Encoding: CP1252. Filename: pda_export_YYYYMMDD.csv.

**Files:** routes/admin.py

---

### 9. PWA Install Button
**Problem:** No install prompt appeared. beforeinstallprompt event not captured.

**Solution:** Added beforeinstallprompt listener in app.js. Custom install button fixed bottom-right. Shows automatically when browser fires event. Hides after install.

**Files:** static/js/app.js, templates/base.html, static/css/app.css

---

### 10. UI Redesign - Duolingo + Apple Health Style
**Problem:** Dark theme felt generic. No premium native app feel. Multiple CSS rewrites needed.

**Solution:** Complete CSS rewrite inspired by Duolingo and Apple Health:
- Light background F5F5F5
- Duolingo green primary 58CC02 with 3D button shadows
- Bold 800 weight typography throughout
- 2px borders instead of 0.5px for definition
- Rounded corners 16-24px
- Active states with translateY for physical button feel
- Colorful category icons (blue, green, orange, purple, teal)
- Grouped list rows like iOS Settings
- Hero card with gradient green background
- Frosted glass scan overlay
- Green glow on scan flash
- Scanner frame with dark overlay outside

**Files:** static/css/app.css

---

## Rules - What NOT To Do

1. Never push *.db files to Git
2. Never use app.run with ssl_context=adhoc in production
3. Never use psycopg2-binary on Railway Python 3.13
4. Never load all records without pagination
5. Never do row-by-row DB queries in import loops
6. Never use Instascan or Quagga for scanning
7. Never define the same CSS class twice
8. Never use position fixed without left right bottom set
9. Never skip min-width 0 on flex children with inputs
10. Never commit without checking git status first
11. Never change working features without understanding why they work
12. Never use regex replacement without verifying with Select-String after
13. Always provide output after each step before moving to next

---

## Scanner Architecture

Device opens /scan
  → initScanner()
    → Is iOS?
      YES → loadZxing() → startCameraIOS()
        → getUserMedia (facingMode only, gets permission)
        → enumerateDevices (pick back camera)
        → ZXing decodeFromConstraints or decodeFromVideoDevice
      NO → Has BarcodeDetector?
        YES → startBarcodeDetector()
          → getUserMedia → createImageBitmap → detect() loop via rAF
        NO → loadZxing() → startCameraIOS() (same ZXing path)

Barcode detected → onBarcodeDetected()
  → Pause scanning + cooldown
  → Flash effect
  → lookupBarcode() → POST /api/lookup
    → Found? → showFound() → showQtyPanel()
    → Not found? → showNotFound() → resumeScanning()

Qty confirmed → confirmAdd()
  → POST /api/add-ligne
  → Update badge count
  → hideQtyPanel()
  → resumeScanning()

---

## PDA vs Camera Scanning

Honeywell PDAs (CT40, CT60, EDA52) use hardware laser/imager engines.
They read barcodes instantly via dedicated chip - not camera.

This app uses camera-based scanning which is slower but:
- Native BarcodeDetector on Android is near-instant
- ZXing on iOS is functional but slower
- Resolution kept at 640x480 to reduce processing
- Scan cooldown at 800ms for snappy feel
- createImageBitmap downscale to 320x240 for fast detection

For warehouse use: pair with a Bluetooth barcode scanner for best results.
The manual input field also accepts keyboard input from BT scanners.

---

## Tech Stack

- Backend: Python 3.13, Flask 3.0, Flask-SQLAlchemy, Flask-Login
- Database: PostgreSQL via pg8000 on Railway
- Frontend: Vanilla JS, CSS custom properties
- Scanner: Native BarcodeDetector + ZXing fallback
- PWA: manifest.json, service worker, beforeinstallprompt
- Deployment: Railway, gunicorn, PostgreSQL addon
- Local dev: SQLite fallback, adhoc SSL via pyopenssl

---

## Production URLs

- App: https://scan-reception-production.up.railway.app
- Admin: https://scan-reception-production.up.railway.app/admin
- Scanner: https://scan-reception-production.up.railway.app/scan

---

## Verified Working On

- Android Chrome/Brave - camera, BarcodeDetector, PWA install, bulk import
- Desktop Chrome/Firefox - admin panel, import, pagination, export
- iOS Safari - camera permission confirmed via Appetize.io
- Railway production - PostgreSQL, persistent data, HTTPS

---

## Next Steps

1. Test iOS Safari scanning on real device
2. Torch/flashlight toggle for dark warehouses
3. Haptic feedback on scan via Vibration API
4. Scan beep sound with user toggle
5. Offline scan queue with sync on reconnect
6. Bluetooth barcode scanner keyboard input support
7. Web Worker for ZXing decoding

---

*Last updated: May 28, 2026*
"@ | Out-File -FilePath "DEVELOPMENT.md" -Encoding utf8












Here is the complete technical document. Save it as `TECHNICAL.md` in your project:

```powershell
@"
# PMD Reception — Technical Documentation
# Honeywell EDA51 PDA Barcode Scanning System

---

## Project Overview

PMD Reception is a mobile-first Progressive Web App (PWA) designed for warehouse product reception workflows.
It runs on a Honeywell EDA51 PDA device using the hardware laser scanner.
The backend is Flask (Python), the database is PostgreSQL (Railway), and the frontend is vanilla JavaScript.

Production URL: https://scan-reception-production.up.railway.app

---

## Hardware

### Honeywell ScanPal EDA51
- OS: Android 8.1
- Browser: Chrome (old version)
- Scanner: Built-in hardware laser/imager (N6603 engine)
- Scanning method: Keyboard Wedge (types barcode as keyboard input + Enter suffix)

### Key Hardware Behavior
- The laser scanner does NOT use the camera
- It types the barcode characters into the focused input field
- It sends a suffix character (configured as \n) after the barcode
- It acts exactly like a USB barcode scanner keyboard
- Speed: types full barcode in under 50ms

---

## Critical PDA Chrome 8.1 Compatibility Rules

### NEVER use POST requests from the scanner page
Old Chrome on Android 8.1 silently blocks POST fetch requests in certain network conditions.
Always use GET requests for scanner API calls.

### ALWAYS use GET for these endpoints
- /api/lookup?barcode=XXXX
- /api/current-reception
- GET is safe and works reliably on old Chrome

### POST is OK ONLY for
- /api/add-ligne (confirmed working with JSON body)
- /api/start-reception (accepts both GET and POST)
- /api/finish-reception (accepts both GET and POST)

### Session Cookies
- Must set SECRET_KEY as environment variable on Railway
- SESSION_COOKIE_SECURE = True
- SESSION_COOKIE_SAMESITE = Lax
- Without proper SECRET_KEY, sessions reset on every redeploy

---

## Honeywell Scanner Settings (Required Configuration)

On the PDA device:
Settings -> Honeywell Settings -> Scanning -> Internal Scanner -> Default Profile -> Data Processing Settings

- Wedge Method: Keyboard
- Suffix: \n (newline)
- Charset: ISO 8859-1

Without these settings the scanner will not send data to the browser input field.

---

## How the Scanner Works in the App

1. User opens /scan page
2. A hidden input field (id="manual-input") is auto-focused
3. User presses the yellow trigger on the side of the PDA
4. Hardware laser reads the barcode
5. Barcode is typed into the hidden input (keyboard wedge)
6. \n suffix triggers the input event listener
7. App detects the barcode via three methods:
   - Method 1: detect \n or \r in input value
   - Method 2: auto-submit after 150ms pause (scanner types faster than human)
   - Method 3: Enter key keydown fallback
8. processBarcode() is called
9. GET /api/lookup?barcode=XXXX is called
10. If found: show article name + quantity panel
11. User confirms quantity
12. POST /api/add-ligne saves to database
13. Input re-focuses automatically for next scan

---

## Project Structure

scan-reception/
├── app.py                          # Flask app factory
├── config.py                       # Config: SECRET_KEY, DATABASE_URL, session settings
├── extensions.py                   # db and login_manager instances
├── requirements.txt                # Python dependencies
├── Procfile                        # Railway: gunicorn app:app --timeout 300 --workers 1 --threads 4
├── .gitignore                      # Excludes: *.db, venv/, __pycache__/, .env
├── models/
│   ├── article.py                  # Article: code_article, barcode, designation, unite
│   ├── fournisseur.py              # Fournisseur: nom, contact, telephone
│   ├── reception.py                # Reception + ReceptionLigne + generate_reference()
│   └── user.py                     # User with password hashing
├── routes/
│   ├── admin.py                    # Admin panel: articles, fournisseurs, receptions, import, export
│   ├── api.py                      # JSON API: lookup(GET), add-ligne, start-reception, finish-reception
│   ├── main.py                     # Homepage route
│   └── scan.py                     # Scanner page route
├── static/
│   ├── css/app.css                 # Full mobile-first theme (Duolingo + Apple Health style)
│   ├── js/app.js                   # Toast notifications + PWA install button
│   ├── js/scanner.js               # PDA scanner logic (keyboard wedge input handler)
│   ├── js/vendor/index.min.js      # ZXing library (bundled locally)
│   ├── manifest.json               # PWA manifest
│   ├── sw.js                       # Service worker
│   └── icons/                      # icon-192.png, icon-512.png (company logo)
└── templates/
    ├── base.html                   # Base layout: PWA meta, toast, install button, Dev by Mr Badr
    ├── reception/
    │   ├── index.html              # Homepage: start reception form
    │   ├── scan.html               # PDA scanner page (Scanner Pret card)
    │   └── log.html                # Reception log
    └── admin/
        ├── login.html              # Admin login
        ├── dashboard.html          # Admin dashboard with stats
        ├── articles/
        │   ├── list.html           # Paginated article list (100 per page) with search
        │   ├── form.html           # Create/edit article
        │   └── import.html         # CSV/XLSX bulk import
        ├── fournisseurs/
        │   ├── list.html
        │   └── form.html
        └── receptions/
            ├── list.html           # Receptions with export button per reception
            └── detail.html

---

## Database

### Production
- PostgreSQL on Railway
- Driver: pg8000 (pure Python - psycopg2 does not work on Railway Python 3.13)
- DATABASE_URL set as Railway environment variable
- config.py replaces postgresql:// with postgresql+pg8000://

### Local Development
- SQLite fallback (reception.db)
- reception.db is in .gitignore - NEVER commit it

### Key Models

Article:
- id, code_article (unique), designation, barcode (unique), unite, is_active

Reception:
- id, reference (unique), fournisseur_id, date_reception, notes, statut, created_at
- reference generated by generate_reference() using random 4-digit suffix
- IMPORTANT: never use COUNT-based reference generation (causes duplicates)

ReceptionLigne:
- id, reception_id, article_id, qte_recue, scanned_at

---

## API Endpoints

GET  /api/current-reception         Check if reception session is active
POST /api/start-reception           Start new reception (also accepts GET for PDA)
POST /api/finish-reception          Mark reception as terminated (also accepts GET)
GET  /api/lookup?barcode=XXX        Lookup article by barcode (GET only - PDA compatible)
POST /api/add-ligne                 Add scanned article to reception
DELETE /api/remove-ligne/<id>       Remove a ligne

---

## CSV Import

### Required columns (all mandatory)
- barcode
- code_article
- designation

### Optional columns
- unite (defaults to "piece" if missing)

### Format
- Separator: semicolon (;)
- Encoding: UTF-8 (app also handles latin-1, cp1252 automatically)
- No header row required but column names must match exactly

### Performance
- Uses bulk_save_objects() for fast insertion
- Pre-loads all existing codes and barcodes into memory dicts
- Single db.session.commit() at end
- Handles 7782 articles without timeout

---

## CSV Export

### Per reception export (/admin/receptions/<id>/export)
- Format: barcode;qte
- No header row
- Encoding: CP1252 (required by target PDA system)
- Filename: REC-YYYYMM-XXXX.csv

### Full export (/admin/export)
- Same format
- Can filter by date range
- All receptions combined

---

## Deployment (Railway)

### Environment Variables Required
- DATABASE_URL: postgresql://... (set by Railway PostgreSQL addon)
- SECRET_KEY: any long random string
- LD_LIBRARY_PATH: /usr/lib/x86_64-linux-gnu (if needed)

### Procfile
web: gunicorn app:app --timeout 300 --workers 1 --threads 4

### Why these settings
- --timeout 300: needed for large CSV imports (7782 articles)
- --workers 1: pg8000 is not thread-safe with multiple workers
- --threads 4: allows concurrent requests within single worker

---

## What NOT To Do (Lessons Learned)

1. NEVER use psycopg2-binary on Railway Python 3.13 - use pg8000
2. NEVER use COUNT-based reference generation - causes IntegrityError on concurrent requests
3. NEVER push *.db files to Git
4. NEVER use app.run() with ssl_context=adhoc in production
5. NEVER use overflow:hidden on body or app-shell - breaks page scrolling
6. NEVER define the same CSS class twice - causes unpredictable overrides
7. NEVER use regex to patch files - always rewrite entire file
8. NEVER change working features without understanding why they work
9. NEVER use POST requests from PDA Chrome 8.1 for lookup operations
10. NEVER use COUNT for unique reference generation in concurrent environments
11. NEVER forget to fix encoding after PowerShell file writes (use UTF8Encoding::new(false))
12. NEVER cherry-pick commits without checking for conflicts first
13. ALWAYS test on the actual PDA after every change
14. ALWAYS provide entire file content when making HTML/CSS/JS changes
15. ALWAYS verify git log before and after rollbacks

---

## Common Errors and Solutions

### IntegrityError: duplicate key value violates unique constraint receptions_reference_key
Cause: generate_reference() uses COUNT which creates same reference on concurrent requests
Fix: Use random 4-digit suffix and check existence in a while loop

### UnicodeDecodeError: utf-8 codec cant decode byte
Cause: PowerShell writes files in UTF-16 or Windows-1252 by default
Fix: Always use [System.IO.File]::WriteAllText with [System.Text.UTF8Encoding]::new(false)

### psycopg2 ImportError: libpq.so.5 not found
Cause: psycopg2-binary requires system PostgreSQL libraries not available on Railway
Fix: Use pg8000 driver and update DATABASE_URL prefix to postgresql+pg8000://

### 500 Error on admin pages after file edit
Cause: Template file saved with wrong encoding (non-UTF8 characters)
Fix: Re-save file with proper UTF-8 encoding without BOM

### PDA scanner not submitting barcode
Cause: Enter key not being sent or input not focused
Fix: Three-method detection (newline in value, 150ms timer, keydown Enter)
Also check: Honeywell settings Wedge Method=Keyboard, Suffix=\n

### Black camera area on scan page
Cause: Old camera-based scanner code still present
Fix: Use PDA-only scan page with hidden input and Scanner Pret card

### Page cannot scroll (pagination not reachable)
Cause: overflow:hidden on html/body or .app-page
Fix: Remove overflow:hidden from html, body, .app-shell, .app-page

---

## Scanner Architecture

User presses PDA trigger
  -> Hardware laser reads barcode
  -> Keyboard wedge types barcode into hidden #manual-input
  -> Suffix \n arrives
  -> input event fires
    -> Method 1: detect \n in value -> processBarcode()
    -> Method 2: 150ms timeout -> processBarcode()
    -> Method 3: keydown Enter -> processBarcode()
  -> GET /api/lookup?barcode=XXXX
    -> Article found -> showFound() -> showQtyPanel()
    -> Article not found -> showNotFound() -> resumeScanning()
  -> User confirms quantity
  -> POST /api/add-ligne {article_id, qte}
  -> Badge count updated
  -> Panel closes
  -> Input re-focused
  -> Ready for next scan

---

## Tech Stack

Backend:    Python 3.13, Flask 3.0, Flask-SQLAlchemy, Flask-Login
Database:   PostgreSQL (Railway) via pg8000 driver
Frontend:   Vanilla JavaScript, CSS custom properties
Scanner:    Honeywell EDA51 hardware laser (keyboard wedge mode)
PWA:        manifest.json, service worker, beforeinstallprompt
Deployment: Railway.app, Gunicorn WSGI server
Local dev:  SQLite fallback, Python venv

---

## Verified Working On

- Honeywell EDA51 (Android 8.1, Chrome) - Primary device
- Desktop Chrome/Firefox - Admin panel
- Android phone Chrome - Camera scanning (BarcodeDetector)
- Railway production - PostgreSQL, HTTPS, persistent data

---

## Future Improvements

1. Torch/flashlight toggle for dark warehouses
2. Haptic feedback on successful scan (Vibration API)
3. Offline scan queue with sync on reconnect
4. Barcode sound beep on detection
5. Web Worker for ZXing decoding (if camera scanning added back)
6. End-to-end tests with Playwright
7. Export filtered by fournisseur
8. User authentication per operator (not just admin)
9. Print reception report as PDF

---

*Last updated: June 3, 2026*
*Developed by Mr Badr*
"@ | Out-File -FilePath "TECHNICAL.md" -Encoding utf8
```

Then push:

```powershell
git add .
git commit -m "Docs: complete TECHNICAL.md - PDA scanning system documentation"
git push
```

Paste the output.



Here is the complete technical log. Paste this entire content into `TECHNICAL.md` in VSCode:

```markdown
# PMD Reception — Complete Technical Documentation
# Honeywell EDA51 PDA Barcode Scanning System
# Developed by Mr Badr

---

## Table of Contents
1. Project Overview
2. Hardware
3. Tech Stack
4. Project Structure
5. Database Schema
6. API Endpoints
7. Frontend Architecture
8. Scanner Logic (Full Code Explained)
9. Service Worker & Caching
10. CSV Import & Export
11. Admin Panel
12. Deployment (Railway)
13. Environment Variables
14. Critical Rules — What NOT To Do
15. Common Errors & Solutions
16. Full Development Changelog
17. Future Improvements

---

## 1. Project Overview

PMD Reception is a mobile-first Progressive Web App (PWA) built for warehouse product reception workflows.
It runs on a Honeywell EDA51 PDA device using the built-in hardware laser scanner.
When an agent scans a barcode, the system identifies the article, the agent confirms the quantity,
and the data is saved to a cloud PostgreSQL database in real time.
The manager (M. Anass) can then export the reception data in the exact format required by the target system.

Production URL: https://scan-reception-production.up.railway.app
GitHub: https://github.com/eddinemoonmoon-hub/scan-reception

---

## 2. Hardware

### Honeywell ScanPal EDA51
- OS: Android 8.1
- Browser: Chrome (older version)
- Scanner engine: Built-in N6603 laser/imager
- Scanning method: Keyboard Wedge
- Communication: WiFi only (no cables)

### How the Keyboard Wedge Works
The Honeywell EDA51 does not use the camera for scanning.
When the agent presses the yellow trigger:
1. The laser reads the barcode in under 50ms
2. The barcode digits are "typed" into the focused browser input field (like a keyboard)
3. A suffix character (\n newline) is sent automatically after the barcode
4. The app detects this and processes the barcode

### Required PDA Configuration
Go to: Settings -> Honeywell Settings -> Scanning -> Internal Scanner -> Default Profile -> Data Processing Settings
- Wedge Method: Keyboard
- Suffix: \n (newline)
- Charset: ISO 8859-1

---

## 3. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, Flask 3.0 |
| ORM | Flask-SQLAlchemy 3.1.1 |
| Auth | Flask-Login 0.6.3 |
| Database (prod) | PostgreSQL via pg8000 1.30.3 |
| Database (local) | SQLite (fallback) |
| WSGI Server | Gunicorn 21.2.0 |
| Frontend | Vanilla JavaScript, CSS Custom Properties |
| PWA | manifest.json, Service Worker |
| Deployment | Railway.app |
| Version Control | Git / GitHub |

### Why pg8000 and not psycopg2
psycopg2-binary requires system-level PostgreSQL libraries (libpq.so.5) which are NOT available
on Railway's Python 3.13 environment. pg8000 is a pure Python PostgreSQL driver that works
without any system dependencies.

---

## 4. Project Structure

```
scan-reception/
├── app.py
├── config.py
├── extensions.py
├── requirements.txt
├── Procfile
├── .gitignore
├── TECHNICAL.md
├── DEVELOPMENT.md
├── models/
│   ├── __init__.py
│   ├── article.py
│   ├── fournisseur.py
│   ├── reception.py
│   └── user.py
├── routes/
│   ├── __init__.py
│   ├── admin.py
│   ├── api.py
│   ├── main.py
│   └── scan.py
├── static/
│   ├── css/
│   │   └── app.css
│   ├── js/
│   │   ├── app.js
│   │   ├── scanner.js
│   │   └── vendor/
│   │       └── index.min.js
│   ├── icons/
│   │   ├── icon-192.png
│   │   └── icon-512.png
│   ├── manifest.json
│   └── sw.js
└── templates/
    ├── base.html
    ├── errors/
    │   ├── 404.html
    │   └── 500.html
    ├── reception/
    │   ├── index.html
    │   ├── scan.html
    │   └── log.html
    └── admin/
        ├── login.html
        ├── dashboard.html
        ├── articles/
        │   ├── list.html
        │   ├── form.html
        │   └── import.html
        ├── fournisseurs/
        │   ├── list.html
        │   └── form.html
        └── receptions/
            ├── list.html
            └── detail.html
```

---

## 5. Database Schema

### Article
```python
class Article(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    code_article = db.Column(db.String(50), unique=True, nullable=False)
    designation  = db.Column(db.String(200), nullable=False)
    barcode      = db.Column(db.String(100), unique=True, nullable=True)
    unite        = db.Column(db.String(20), default='piece')
    is_active    = db.Column(db.Boolean, default=True)
```

### Fournisseur
```python
class Fournisseur(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    nom       = db.Column(db.String(100), nullable=False)
    contact   = db.Column(db.String(100), nullable=True)
    telephone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
```

### Reception
```python
class Reception(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    reference      = db.Column(db.String(50), unique=True, nullable=False)
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseurs.id'), nullable=True)
    date_reception = db.Column(db.Date, default=datetime.utcnow)
    notes          = db.Column(db.Text, nullable=True)
    statut         = db.Column(db.String(20), default='en_cours')
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def generate_reference():
        import random
        now = datetime.utcnow()
        while True:
            ref = f"REC-{now.year}{now.month:02d}-{random.randint(1000, 9999)}"
            if not Reception.query.filter_by(reference=ref).first():
                return ref
```

### ReceptionLigne
```python
class ReceptionLigne(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    reception_id = db.Column(db.Integer, db.ForeignKey('receptions.id'), nullable=False)
    article_id   = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    qte_recue    = db.Column(db.Float, nullable=False, default=1)
    scanned_at   = db.Column(db.DateTime, default=datetime.utcnow)
```

---

## 6. API Endpoints

### Scanner Endpoints (PDA Compatible - GET only)
```
GET  /api/current-reception
     Returns: {active: bool, reference, total_lignes, lignes[]}

GET  /api/lookup?barcode=XXXX
     Returns: {found: bool, article: {id, code_article, designation, unite, barcode}}

GET/POST  /api/start-reception?fournisseur_id=X&notes=Y
     Returns: {success: bool, reception_id, reference}

GET/POST  /api/finish-reception
     Returns: {success: bool, reference}
```

### Data Endpoints (POST)
```
POST /api/add-ligne
     Body: {article_id, qte}
     Returns: {success: bool, total_lignes, lignes[]}

DELETE /api/remove-ligne/<id>
     Returns: {success: bool}
```

### Why GET for lookup
Old Chrome on Android 8.1 (Honeywell EDA51) silently blocks POST fetch requests
in certain conditions. GET requests always work reliably.
The lookup endpoint was changed from POST to GET to fix this issue permanently.

---

## 7. Frontend Architecture

### base.html
- PWA meta tags (apple-mobile-web-app-capable, theme-color)
- manifest.json link
- app.css link
- app.js (toast + PWA install button)
- Service worker registration
- "Dev by Mr Badr" signature

### app.js
- showToast(msg, type) — notification system
- PWA install button (beforeinstallprompt event)
- formatQty(v) — number formatting utility

### scanner.js (PDA version)
The scanner.js is the core of the app for PDA use.
It does NOT use the camera. It only listens for keyboard input from the hardware laser.

Full scanner flow:
```javascript
// 1. On page load - focus hidden input
setupScanner() {
  var manualInput = document.getElementById("manual-input");
  manualInput.focus();

  // Keep focus on input
  setInterval(function() {
    if (!isPaused) manualInput.focus();
  }, 800);

  // Method 1: detect newline suffix from Honeywell scanner
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
    if (e.key === "Enter") {
      var barcode = manualInput.value.trim();
      manualInput.value = "";
      if (barcode.length >= 4) processBarcode(barcode);
    }
  });
}

// 2. Lookup article
function processBarcode(barcode) {
  fetch("/api/lookup?barcode=" + encodeURIComponent(barcode))
    .then(r => r.json())
    .then(data => {
      if (data.found) showFound(data.article);
      else showNotFound(barcode);
    });
}

// 3. Show quantity panel
function showQtyPanel(article) {
  document.getElementById("qty-input").value = "1";
  document.getElementById("qty-panel").classList.add("visible");
}

// 4. Confirm and save
function confirmAdd() {
  var qte = parseFloat(document.getElementById("qty-input").value) || 1;
  fetch("/api/add-ligne", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({article_id: currentArticle.id, qte: qte})
  });
}
```

### scan.html (PDA Page)
No camera. No video element. Clean PDA interface:
- Header with reception reference and badge count
- "Scanner Pret" card with laser icon
- Hidden input (#manual-input) always focused
- Article found/not found state cards
- Quantity panel (slides up from bottom)
- Manual search input (visible, for manual barcode entry)
- Finish reception button
- Bottom navigation

### CSS Architecture
- CSS custom properties (variables) for theming
- Duolingo + Apple Health inspired design
- Light background (#F5F5F5), bold typography
- Primary green color (#58CC02) with 3D button shadows
- Minimum 48px touch targets
- Safe-area insets for notch/home bar
- No overflow:hidden on body or app-shell (critical for scrolling)
- Qty panel: position fixed, slides up with translateY animation

---

## 8. Scanner Logic Deep Dive

### Why 3 detection methods
The Honeywell EDA51 can behave slightly differently depending on:
- Scanner settings
- Android version
- Chrome version
- Network conditions

Method 1 (newline detection) catches the \n suffix configured in PDA settings.
Method 2 (150ms timer) catches cases where the suffix is not sent or arrives late.
Method 3 (Enter keydown) is a final safety net.

### Why 150ms timeout
A human typing a 13-digit barcode takes at least 500ms.
The Honeywell laser types the full barcode in under 50ms.
So 150ms is the perfect threshold:
- Human typing: never triggers (pauses between keys)
- Laser scan: always triggers (all chars in one burst)

### Hidden input design
The input (#manual-input) is:
- Positioned absolute with opacity:0 and size 1x1px
- Always re-focused after each scan
- inputmode="none" to prevent software keyboard from opening
- autocomplete, autocorrect, autocapitalize all off

---

## 9. Service Worker & Caching

### Strategy: Stale-While-Revalidate
```javascript
// Serve from cache instantly (fast)
// Then update cache in background (always fresh next load)
cache.match(request).then(function(cached) {
  var fetchPromise = fetch(request).then(function(response) {
    cache.put(request, response.clone());
    return response;
  }).catch(function() { return cached; });
  return cached || fetchPromise;
});
```

### What is cached (v3)
- /static/css/app.css
- /static/js/app.js
- /static/js/scanner.js
- /static/manifest.json
- /static/icons/icon-192.png
- /static/icons/icon-512.png

### What is NEVER cached
- /api/* (always fresh from server)
- /admin/* (always fresh from server)
- HTML navigation pages (network first)

### Cache versioning
When CACHE_NAME changes (e.g. v3 -> v4), old caches are deleted on activate.
Update the version number whenever you make significant CSS/JS changes.

---

## 10. CSV Import & Export

### Import (/admin/articles/import)

Required columns:
- barcode (mandatory - core of the system)
- code_article (mandatory)
- designation (mandatory)
- unite (optional, defaults to "piece")

Format:
- Separator: semicolon (;)
- Encoding: UTF-8 (app auto-detects latin-1, cp1252 as fallback)
- With or without header row

Performance optimization for 7782 articles:
```python
# Pre-load all existing into memory (avoid per-row DB queries)
existing_codes = {a.code_article: a for a in Article.query.all()}
existing_barcodes = {a.barcode: a for a in Article.query.filter(Article.barcode != None).all()}

# Bulk save new articles
if new_articles:
    db.session.bulk_save_objects(new_articles)
db.session.commit()  # Single commit at end
```

### Export per Reception (/admin/receptions/<id>/export)
Format:
```
6111252421728;5
6111252420301;10
6111252420240;3
```
- No header row
- Separator: semicolon (;)
- Encoding: CP1252 (required by target system)
- Filename: REC-YYYYMM-XXXX.csv

### Full Export (/admin/export)
Same format, all receptions combined, filterable by date range.

---

## 11. Admin Panel

### Authentication
Simple password-based (session cookie).
Default password: admin123
Change via ADMIN_PASSWORD in config.py or environment variable.

### Articles List
- Pagination: 100 articles per page
- Search by code_article, designation, barcode
- Toggle active/inactive
- Edit individual articles
- Delete (blocked if used in receptions)
- Import CSV/XLSX
- Scrolling fixed (no overflow:hidden on container)

### Receptions List
- Filter by date range
- Export all as CSV (header button)
- Export individual reception as CSV (green button per row)
- Delete reception
- View detail

### Fournisseurs
- Full list (no pagination needed - small number)
- Create, edit, toggle active

---

## 12. Deployment (Railway)

### Services
1. scan-reception (Flask app)
2. PostgreSQL (database addon)

### Build Process
Railway detects Python app automatically.
Uses requirements.txt for dependencies.
Uses Procfile for start command.

### Procfile
```
web: gunicorn app:app --timeout 300 --workers 1 --threads 4
```

Why these settings:
- --timeout 300: CSV import of 7782 articles needs more than 30s default
- --workers 1: pg8000 is not thread-safe with multiple workers sharing connections
- --threads 4: allows concurrent requests within single worker

### Auto-deploy
Every git push to main branch triggers automatic Railway redeploy.
No manual action needed after git push.

---

## 13. Environment Variables

Set these in Railway -> Service -> Variables:

| Variable | Value | Required |
|----------|-------|----------|
| DATABASE_URL | postgresql://... (auto-set by Railway PostgreSQL addon) | Yes |
| SECRET_KEY | any long random string | Yes |

### config.py logic
```python
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+pg8000://', 1)
elif DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+pg8000://', 1)
```

---

## 14. Critical Rules — What NOT To Do

1. NEVER use psycopg2-binary on Railway Python 3.13
   Use pg8000 instead.

2. NEVER use COUNT-based reference generation
   Causes IntegrityError on concurrent requests.
   Always use random + existence check loop.

3. NEVER push *.db files to Git
   reception.db is in .gitignore.

4. NEVER use app.run() with ssl_context=adhoc in production
   Railway handles HTTPS automatically.

5. NEVER add overflow:hidden to html, body, .app-shell, or .app-page
   This breaks page scrolling and hides pagination buttons.

6. NEVER define the same CSS class twice
   Always remove the old definition before adding new one.

7. NEVER use regex to patch files
   Always rewrite the entire file to avoid stacking errors.

8. NEVER change working features without understanding why they work
   Always read and understand existing code before modifying.

9. NEVER use POST requests for lookup from PDA Chrome 8.1
   Old Chrome silently blocks POST in certain conditions.
   Use GET with query parameters instead.

10. NEVER forget UTF-8 encoding when saving files with PowerShell
    Always use: [System.IO.File]::WriteAllText(path, content, [System.Text.UTF8Encoding]::new($false))

11. NEVER cherry-pick commits without checking for conflicts first
    Use git status after cherry-pick to check for conflicts.

12. ALWAYS test on the actual PDA after every change
    Desktop Chrome behavior differs from Android 8.1 Chrome.

13. ALWAYS provide the entire file content when making changes
    Never use partial regex replacements on HTML/CSS/JS/Python files.

14. ALWAYS verify git log before and after rollbacks
    Use: git log --oneline -10

15. ALWAYS bump the service worker CACHE_NAME version after major CSS/JS changes
    Example: pmd-reception-v3 -> pmd-reception-v4

---

## 15. Common Errors & Solutions

### IntegrityError: duplicate key value violates unique constraint receptions_reference_key
```
Cause: generate_reference() used COUNT which creates same reference on concurrent requests
Fix:   Use random 4-digit suffix with existence check loop in models/reception.py
```

### UnicodeDecodeError: utf-8 codec cant decode byte 0xXX
```
Cause: Template file saved with wrong encoding by PowerShell (Windows-1252 or UTF-16)
Fix:   Re-save file: [System.IO.File]::WriteAllText(path, content, [System.Text.UTF8Encoding]::new($false))
```

### ImportError: libpq.so.5 cannot open shared object file
```
Cause: psycopg2-binary requires system PostgreSQL libraries not on Railway Python 3.13
Fix:   Use pg8000==1.30.3 in requirements.txt
       Update DATABASE_URL prefix to postgresql+pg8000://
```

### 500 Error after file edit
```
Cause: Template saved with non-UTF8 characters
Fix:   Re-save with proper UTF-8 encoding without BOM
```

### PDA scanner not submitting barcode (barcode stays in field)
```
Cause: Input not focused or Enter key not being detected
Fix:   Check Honeywell settings: Wedge Method=Keyboard, Suffix=\n
       Check scanner.js has all 3 detection methods active
       Check setInterval re-focus is running every 800ms
```

### Black camera area on scan page
```
Cause: Old camera-based scanner code still in scan.html or scanner.js
Fix:   Use PDA-only scan page with pda-ready-card and hidden input
       Remove all video/camera elements from scan.html
```

### Page cannot scroll / pagination button not reachable
```
Cause: overflow:hidden on html, body, .app-shell, or .app-page
Fix:   Search CSS for overflow:hidden and remove from these selectors
       Keep overflow:hidden only on scanner elements and list containers
```

### Erreur lors du demarrage (start reception fails)
```
Cause: Usually IntegrityError from duplicate reference OR POST blocked on PDA Chrome
Fix:   Check generate_reference() uses random method
       Check /api/start-reception accepts GET method
```

### Service worker serving stale files after deployment
```
Cause: CACHE_NAME not updated, old cache still served
Fix:   Bump CACHE_NAME version in static/sw.js (e.g. v3 -> v4)
       This forces old cache deletion on next activate event
```

---

## 16. Full Development Changelog

### Phase 1: Initial Setup
- Flask app factory pattern with blueprints
- SQLite local database
- Basic article, fournisseur, reception models
- Simple admin panel with CRUD operations
- Basic scan page with camera

### Phase 2: Camera Scanner (Abandoned for PDA)
- Tried Instascan CDN (dead/unreliable)
- Tried Quagga (laggy, black screen on mobile)
- Tried ZXing BrowserMultiFormatReader
- Tried native BarcodeDetector API
- Tried iOS Safari canvas loop
- Tried ImageCapture.grabFrame() (not supported on iOS Safari)
- Decision: Abandon camera scanning entirely for PDA hardware laser

### Phase 3: PDA Hardware Integration
- Switched to keyboard wedge input model
- Hidden input always focused
- 3-method barcode detection (newline, timer, Enter)
- Redesigned scan page: Scanner Pret card, no camera
- Fixed PDA Chrome 8.1 POST blocking: changed lookup to GET
- Fixed reference generation: COUNT -> random + existence check

### Phase 4: Production Deployment
- Moved from SQLite to PostgreSQL on Railway
- Fixed psycopg2 -> pg8000 driver issue
- Added Procfile with proper gunicorn settings
- Added .gitignore for *.db files
- Configured environment variables on Railway
- Fixed session cookie settings for production HTTPS

### Phase 5: Performance & Admin
- Bulk import with bulk_save_objects (7782 articles)
- Pagination on articles list (100 per page)
- Export per reception (CP1252 format)
- Full export with date filter
- Service worker v3 with stale-while-revalidate
- Scrolling fixed (removed overflow:hidden from app containers)

### Phase 6: Design & Branding
- Duolingo + Apple Health inspired theme
- Company logo replacing SVG placeholder
- Dev by Mr Badr signature in base.html
- Green primary color (#58CC02) with 3D button effects
- Qty panel fixed positioning with slide animation
- Mobile touch targets minimum 48px

---

## 17. Future Improvements

1. Offline scan queue with background sync
   - Save scans to IndexedDB when offline
   - Sync to server when connection returns

2. Torch/flashlight toggle
   - For dark warehouse environments
   - track.applyConstraints({advanced: [{torch: true}]})

3. Haptic feedback on scan
   - navigator.vibrate(50) on successful scan

4. Export filtered by fournisseur
   - Add fournisseur filter to export endpoint

5. User authentication per operator
   - Each agent has login credentials
   - Reception linked to specific agent

6. Print reception report as PDF
   - Generate PDF from reception detail page

7. Real-time dashboard
   - Live reception count on admin dashboard
   - WebSocket or polling

8. Barcode validation
   - Validate EAN-13 checksum before lookup
   - Reject invalid barcodes early

9. Quantity limits
   - Set expected quantity per article
   - Alert when scanned quantity exceeds expected

10. Multi-warehouse support
    - Multiple locations/warehouses
    - Articles assigned to specific warehouses

---

## Appendix: Key Files Content Summary

### requirements.txt
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
WTForms==3.1.1
openpyxl==3.1.2
gunicorn==21.2.0
pg8000==1.30.3
```

### Procfile
```
web: gunicorn app:app --timeout 300 --workers 1 --threads 4
```

### .gitignore
```
venv/
__pycache__/
*.pyc
*.pyo
*.db
.env
.DS_Store
Thumbs.db
```

---

*Last updated: June 3, 2026*
*Developed by Mr Badr*
*PMD Reception — Honeywell EDA51 PDA Barcode Scanning System*
```

---

After pasting in VSCode, push:

```powershell
git add .
git commit -m "Docs: complete TECHNICAL.md - full project documentation"
git push
```