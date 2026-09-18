# ICST AI Food Ordering System — Audit & Fix Report

This document records the audit, the fixes applied, how to run the system, and
what remains out of scope (and why).

## ▶️ How to run (Windows)

```bat
start_app.bat
```

or manually:

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://localhost:5000** in **Chrome or Edge** (voice uses the Web
Speech API, which those browsers support).

**Demo login:** `student@icst.edu.lk` / `ai2024` (created automatically).

---

## 🔴 The critical bug (why nothing worked before)

The frontend (`student.js`) calls `http://localhost:5000` for **both** auth/menu/
order endpoints **and** the voice/food-AI endpoints. Those were served by **two
different Flask apps** (`backend_server.py` and `backend_api.py`) that **both
bound port 5000** — so only one could run at a time, and half the app always 404'd.

**Fix:** a single consolidated server, **`app.py`**, now serves *every* endpoint
the frontend calls. The three superseded servers were moved to `legacy/`.

---

## ✅ Fixes by area

### Backend (new `app.py`)
- **One server, all routes:** `/api/auth/login`, `/api/auth/signup`, `/api/menu`,
  `/api/orders` (GET/POST), `/api/train`, `/api/chat`, `/api/parse-voice-order`,
  `/api/food-image`, `/api/run-voice*`, `/api/run-food-ai*`, `/api/health`, and it
  serves `student.html` at `/`.
- **SQLite** (`app_data.db`, auto-created & seeded from `menu_dataset.json`) — no
  MongoDB install needed. Previously every auth/menu/order call returned
  `503 MongoDB not available`.
- **Order totals are computed server-side** from item price × qty (never trust the
  client).

### Database
- Schema with `users`, `menu`, `orders` and a foreign key.
- Menu names cleaned on import (`.title()` fixes "chicken Rotti" / "Vegitable").
- All queries are **parameterised** → no SQL injection.

### Authentication & Security
- Passwords **hashed** with `werkzeug.security` (was plaintext `==` comparison).
- **Signed, expiring tokens** via `itsdangerous` (7-day TTL) returned on
  login/signup (frontend stores them).
- Login uses one generic error → no user-enumeration.
- Email domain + length validation server-side (not just client-side).
- **Input sanitisation** (`sanitize()`) strips HTML/control chars → prevents stored XSS.
- Chat user input is HTML-escaped in the UI (`escapeHtml`).
- Secret key from `APP_SECRET_KEY` env var (random fallback in dev).

### AI Chatbot
- **`sendChat()` was defined 3×** in `student.js`; the last (a hardcoded canned
  reply) overrode the smart one, so every message got the same answer. Collapsed to
  **one async** `sendChat()` that calls `/api/chat`.
- **Off-topic detection:** non-food questions get
  *"Sorry, this question is not related to our food system."* — localized to
  English, Sinhala, Tamil, Hindi, Spanish.
- Food relevance is detected via multilingual keywords + live menu names.

### Voice system (redesigned)
- The old buttons asked the **server** to open a microphone via a Python
  subprocess — it can never reach the user's mic in a browser. **Replaced with the
  browser Web Speech API:**
  - **STT:** `SpeechRecognition` in the selected language (en/si/ta/hi/es).
  - **TTS:** `speechSynthesis` with a **natural male voice** (`getPreferredVoice`).
  - **Mic permission errors** are caught and shown clearly.
- Spoken/typed orders are parsed by `/api/parse-voice-order` (real quantity + item +
  special-instruction NLP, with precision fixes so "chicken" no longer matches every
  chicken dish).

### Image system
- New **`/api/food-image`** endpoint: validates **file type** (png/jpg/jpeg/webp/gif)
  and **size** (≤5 MB), **compresses/resizes** via Pillow (falls back to storing the
  original if Pillow is absent), and returns the stored URL.
- Frontend "food recognition" buttons now open a **file picker**, upload, and show a
  preview with an **`onerror` fallback** if the image can't render.
- *(True generative image creation needs a paid external API + keys — see Out of scope.)*

### Frontend cleanup / performance
- Removed a **~24-line duplicated block** (fraud/pricing/BMI/mood/nutrition/chat were
  all defined twice).
- All **31 HTML event handlers verified** to resolve to a defined function; **0
  duplicate function definitions** remain. `node --check` passes.
- `addToCart(id, special)` now carries special instructions from voice orders.

### Project structure
- `app.py` is the single entry point. `requirements.txt`, `start_app.bat`,
  `.gitignore` added. `legacy/` holds the retired servers.

---

## 🧪 Verified
Booted the real server and confirmed over HTTP: health 200, login 200 (+token) /
bad-login 401, signup domain validation 400, menu 55 items, order total computed,
order history, multilingual off-topic chat, voice parser precision, image upload +
compression, bad-extension rejected (415), and `GET /` serves the app (200).

---

## 🌐 Multilingual voice fix (2026-06-10)

**Headline issue: "Tamil & Sinhala voice ordering not working" — three separate causes:**

1. **Parser was ASCII-only (the real end-to-end bug).** `parse_voice_order`
   did `re.findall(r"[a-z]+", text)`, which deletes every Tamil/Sinhala
   character — so even a perfect Tamil transcript matched **nothing**.
   **Fixed:** added `FOOD_LEXICON` + `FOREIGN_NUMS` (Tamil & Sinhala food terms
   and number words) and `normalize_multilingual()`, which rewrites the
   transcript to English keywords/digits *before* matching. Quantity detection
   now reads numbers **before or after** the dish (Sinhala/Tamil word order).
   Verified: `கோழி கொத்து இரண்டு` and `කුකුල් කොත්තු දෙක` → 2× Chicken Kottu.

2. **Sinhala speech-to-text is a hard browser limit.** Chrome/Edge Web Speech
   API supports `ta-IN` and `hi-IN` but **not `si-LK`**. Cannot be fixed in
   code. **Mitigated:** voice card now has a language selector; choosing
   Sinhala warns the user and falls back to typed order entry; all Web Speech
   error codes (`no-speech`, `audio-capture`, `network`,
   `language-not-supported`, `not-allowed`) now show clear messages.

3. **TTS depends on OS-installed voices.** Windows ships no Sinhala voice and
   Tamil only if the language pack is installed. **Mitigated:** `speak()` warns
   once per language when no matching voice exists, and still attempts playback.

## 📦 Checkout + Order Tracking (2026-06-10)

Added a real order lifecycle on top of the existing cart/checkout:

- **Time-based status progression** (no POS needed): orders advance
  `placed → preparing → ready → completed` on a timeline computed from the
  order timestamp at read time (`live_status()` in app.py). No background job.
- **New endpoints:** `GET /api/orders/<id>` (live status + step flow for
  polling) and `POST /api/orders/<id>/cancel` (allowed only while placed/preparing;
  returns 409 otherwise, 404 for unknown orders).
- **`order_to_dict` now returns** live `status`, `eta_minutes`, and `cancellable`.
- **Bug fixed:** `order_id` used second-precision `strftime`, so two orders in
  the same second collided on the PRIMARY KEY and the 2nd crashed with a 500.
  Now suffixed with `secrets.token_hex(2)`.
- **Frontend:** Order History cards now show a visual progress tracker
  (Placed/Preparing/Ready/Completed), live ETA, a **Cancel order** button, and
  poll the server every 12 s while any order is in progress (auto-stops when
  done). Added an explicit **remove (🗑️) button** to each cart row and a
  `removeFromCart()` handler. New CSS: `.track-steps`, status pills for
  preparing/completed/cancelled.

Verified over HTTP: place → track (placed→preparing→ready→completed) → cancel
rules (409 when completed, 404 when unknown), unique IDs for same-second orders.

## 🆕 New features (2026-06-10)

### Expanded menu — 55 → 185 items
- `menu_dataset.json` grew by 130 dishes across **10 cuisines** (Sri Lankan,
  Indian, Chinese, Western, Italian, Arabic, Fast Food, Seafood, Vegetarian,
  Vegan). Added a **`cuisine`** field; `category` still uses the 6 meal-time
  buckets so the existing filter bar/UI is untouched.
- `app.py` seeding now **migrates** (`ALTER TABLE menu ADD COLUMN cuisine`) and
  **adds only new ids** on boot — growing the dataset adds foods without
  clobbering admin-edited rows. `GET /api/menu?cuisine=X` filter added.
- Voice lexicon extended with pizza/burger/soup/salad/prawn/crab/paneer/naan/dosa
  in Tamil & Sinhala.

### Admin dashboard (`/admin`)
- New `admin.html` + `admin.js` (self-contained, matches the dark/orange theme).
  Login: **`admin@icst.edu.lk` / `admin2024`** (seeded; `is_admin` flag added to
  users with migration).
- Tabs: **Dashboard** (revenue, order/user/menu counts, popular items, status
  breakdown), **Menu** (search/filter + add/edit/delete), **Orders** (all orders,
  set status), **Users** (list + order counts).
- Backend `/api/admin/*` routes are all gated by `require_admin()` — non-admins
  and anonymous callers get **403**. Verified.

### Image recognition via Gemini Vision
- `/api/food-image` now calls **Gemini Vision** (stdlib `urllib`, no new dep) to
  identify the dish, then matches it to a menu item (word-overlap, prefers the
  most specific match). Returns `recognition: {dish, confidence, menu_match}`.
- **Env-gated & graceful:** set `GEMINI_API_KEY` (+ optional `GEMINI_MODEL`) in
  `.env` to enable; without it, upload/compression still works and recognition is
  simply skipped. Any API error degrades silently to a normal upload.
- Frontend shows the recognised dish + an **"Add to cart"** button for the match.

## ⛔ Out of scope (needs resources/decisions, not code)
- **Generative food-image creation/regeneration** — requires a paid image API
  (OpenAI/Stability/etc.) and keys; `.env` is empty. The upload/optimise/fallback
  pipeline is in place to plug a provider into `/api/food-image`.
- **ML model training** (`training_pipeline.py`, `food_recognition_*.py`) — needs
  heavy deps (torch/tensorflow) and data; left as research code.
- **Live STT/TTS quality** depends on the user's browser/OS installed voices.
- **Google login / payment gateway / admin dashboard** — no implementation exists in
  the current codebase to fix; these are new builds. Happy to add them next.
