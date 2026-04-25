# AI Music Generator — Project Context & Progress Checklist

**Project:** AI Music Generator Web App
**Author:** Chachalit Khanarat — Hong Software Co.
**SRS Version:** 1.0 (dated 29/01/2026)
**Last Updated:** 2026-04-25

---

## 1. Project Context

### What This Project Is
A Django web application where registered users can generate unique AI music tracks by submitting parameters (song name, genre, mood, occasion, singer style, topic) to a third-party API. The system manages a token-based credit economy, a personal music library, and public sharing.

### Who Uses It

| Actor | What They Can Do |
|-------|-----------------|
| **Registered User (Creator)** | Log in, generate tracks, manage library, share tracks via link |
| **Administrator** | Manage all users via Django Admin, adjust token balances |
| **Public Listener** | Access a specific `/listen/<token>/` URL to stream a shared track — no login required |

### Core Business Rules
- Every generation costs **1 token**; tokens are deducted before generation starts
- If generation fails or times out, tokens are **automatically refunded**
- Users cannot generate if their token balance is **zero**
- All tracks are **private by default**; users explicitly toggle them public
- Public share links allow **listen-only** access — no Walled Garden bypass for other pages
- Admins can set any user's token balance (0–9999) via Django Admin
- All Admin changes are logged in `django_admin_log` automatically

### Technical Stack
| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13 / Django 6.0.3 |
| Async Tasks | django-q2 (SQLite-backed queue) |
| Auth | Django built-in + django-allauth (Google OAuth) |
| Database | SQLite (dev) |
| Music APIs | Mureka (official) / Suno (unofficial) via Strategy pattern |
| Frontend | Server-rendered HTML, CSS variables, vanilla JS |

---

## 2. Architecture Overview

```
HTTP Request
    │
    ▼
views.py  ──── profanity.py (content filter)
    │
    ├──► controllers/generate_music.py  ──► models/song.py
    ├──► controllers/manage_library.py  ──► models/ (Song, Library, Folder)
    └──► controllers/admin_token.py     ──► models/ (Profile, TokenRecord)
                │
                ▼
          tasks.py (django-q2 worker)
                │
                ▼
          services/  (Strategy Pattern)
            ├── mureka.py  ──► api.mureka.ai
            └── suno.py    ──► api.sunoapi.org
```

**Key design patterns used:**
- **Strategy Pattern** — music provider is swappable; add a new provider by adding one file + one registry entry in `music/services/__init__.py`
- **Controller layer** — all business logic lives in `music/controllers/`; views are thin
- **Bridge pattern** — `_get_or_create_music_user()` in views.py bridges Django's `auth.User` to the domain `music.User` using email as the key; works for both password and Google OAuth login

---

## 3. Database Schema

| Table | Key Columns |
|-------|-------------|
| `music_user` | id, name, email, role |
| `music_profile` | user_id, token_balance |
| `music_tokenrecord` | user_id, amount, type |
| `music_library` | user_id |
| `music_folder` | library_id, name |
| `music_song` | user_id, folder_id, title, genre, mood, occasion, singer_style, topic, duration, status, provider, file_url, is_public, share_token, **created_at**, **updated_at** |
| `django_q_*` | Task queue tables (django-q2) |
| `socialaccount_*` | OAuth account tables (allauth) |
| `account_emailaddress` | Email verification (allauth) |

**Migrations applied:**
- `0001_initial` — all base models
- `0002_song_file_url` — added file_url to Song
- `0003_song_provider` — added provider field to Song
- `0004_song_timestamps` — added created_at, updated_at to Song *(new)*

---

## 4. SRS Requirements Checklist

### Section 4.1 — User Authentication & Access Control

- [x] **REQ-4.1.1 Walled Garden** — unauthenticated users redirected to login on all protected routes (`@login_required`)
- [x] **REQ-4.1.2 OAuth** — Google OAuth via django-allauth; username/password login also retained
- [x] **REQ-4.1.3 Session** — sessions persist until explicit logout (Django default)

### Section 4.2 — Token Management System

- [x] **REQ-4.2.1** — 1 token deducted per generation (`GenerateMusicController.request_generation`)
- [x] **REQ-4.2.2** — Generation blocked with error message if balance < 1 (`InsufficientTokensError`)
- [x] **REQ-4.2.3** — Admins set/modify token balances via Django Admin (`AdminTokenController`)

### Section 4.3 — Music Generation Engine

- [x] **REQ-4.3.1** — Form accepts: Song Name, Occasion, Genre, Singer Style, Mood, Topic
- [x] **REQ-4.3.2 Background Process** — generation offloaded to django-q2 worker; HTTP request returns immediately
- [x] **REQ-4.3.3 Persistence** — user redirected to Library after submit; generation continues in background
- [x] **REQ-4.3.4 Status Tracking** — Global Status Bar polls `/api/generation-status/` every 3 seconds; shows "Generating…", "Ready!", or "Failed"
- [x] **REQ-4.3.5** — 3-minute duration target *(API-dependent; passed as parameter where supported)*
- [x] **REQ-4.3.6** — Export/download: ⬇ Download button streams file via `download_track_view`. Format selector (.mp3 / .wav / .flac) in library.html; `download_track_view` accepts `?format=` param and sets correct Content-Type / filename.
- [x] **REQ-4.3.7 Timeout & Refund** — `mark_failed()` refunds tokens on exception ✅. Timeout updated to 1200 s (20 min) in settings, suno.py, mureka.py, and utils.py.

### Section 4.4 — Music Library & Management

- [x] **REQ-4.4.1** — Completed songs auto-saved to Personal Library
- [x] **REQ-4.4.2** — Users can delete tracks (with confirmation modal)
- [x] **REQ-4.4.3** — Tracks are Private by default
- [x] **REQ-4.4.4** — Toggle Public generates a unique shareable URL (`/listen/<uuid>/`)
- [x] **REQ-4.4.5** — Public Listen Page accessible without login

### Section 4.5 — Media Player

- [x] **REQ-4.5.1** — Mini-player has Play, Pause, Volume, and Seek via HTML5 `<audio controls>`. ⏮ Prev and ⏭ Next buttons added; playlist stored in `localStorage['mp_playlist']` by library.html; base.html JS reads index to navigate. Auto-advances on track end.
- [x] **REQ-4.5.2** — Player persists across page navigation via localStorage state save/restore

### Section 5 — Non-Functional Requirements

- [x] **REQ-5.2.1 Profanity Filter** — title, mood, topic, genre checked against blocklist before generation; tokens NOT deducted on violation
- [x] **REQ-5.2.2 Thai Law Logging** — `GenerationLog` model captures all generation inputs (title, genre, mood, occasion, singer_style, topic, provider, status) on every request; viewable in Django Admin with date filter and search
- [x] **REQ-5.3.1 Password Hashing** — Django's built-in PBKDF2 password hasher is active by default; no plaintext passwords stored
- [x] **REQ-5.3.2 API Security** — all API keys stored in `.env`, never in source code
- [x] **SRS 3.1.2 Theme** — Dark/Light mode toggle, persisted in localStorage
- [x] **SRS 3.1.4 Accessibility** — Font sizes in base.html and all templates use `rem` units. Browser default font-size scaling is respected.
- [x] **SRS 5.6.3 Responsive** — breakpoints at 480px (mobile) and 1024px (tablet)
- [x] **SRS 5.6.2 IE Blocking Modal** — IE11 detection via `document.documentMode`; blocking overlay modal added to base.html.
- [x] **SRS 5.6.2 In-App Browser Prompt** — User-agent detection for Line/Facebook/Instagram/Twitter in-app browsers; dismissible banner added to base.html.
- [x] **SRS 2.6 Inline Tooltips** — All 6 generate form fields have `title` tooltip attributes and `<p class="field-hint">` description text below each field.

---

## 5. Use Case Implementation Status

### UC-01 — Generate and Share Brand-Safe Background Music

| Step | Status | Notes |
|------|--------|-------|
| Navigate to Generate page | ✅ | |
| Fill 6-field form | ✅ | All fields present |
| Token balance check | ✅ | Blocks with error if 0 |
| Profanity filter on inputs | ✅ | `music/profanity.py` |
| Token deduction + async task queued | ✅ | django-q2 |
| Global Status Bar shows "Generating…" | ✅ | JS polling every 3 s |
| User navigates away; generation continues | ✅ | |
| Status Bar updates to "Ready!" | ✅ | Auto-hides after 5 s |
| Track appears in Library | ✅ | Library reloads on completion |
| Playback via mini-player | ✅ | Persistent footer player |
| Toggle to Public | ✅ | |
| Unique share URL generated | ✅ | UUID share_token |
| Public Listener opens link without login | ✅ | `/listen/<token>/` |
| Insufficient tokens error (E1) | ✅ | |
| Profanity violation error (E2) | ✅ | Tokens not deducted |
| Timeout / API failure — token refund (E3) | ✅ | `mark_failed()` in tasks.py |
| Dark Mode toggle during generation (A2) | ✅ | CSS variables + JS |
| Download track (A3) | ✅ | Format selector (.mp3/.wav/.flac) in library; view serves with correct Content-Type |
| E4 — "Queued" status in status bar | ✅ | Status bar now shows "🕐 Queued for generation…" when Song.status == Queued |

### UC-02 — Manage Personal Library & Playback

| Step | Status | Notes |
|------|--------|-------|
| Library lists all tracks (newest first) | ✅ | Ordered by `created_at` |
| Shows Song Name, Genre, Mood, Duration, Privacy | ✅ | |
| Generating / Failed status badges | ✅ | Animated pulse for Generating |
| Click Play → mini-player starts | ✅ | |
| Navigate away → music continues | ✅ | localStorage state |
| Delete → confirmation modal | ✅ | Custom CSS modal |
| Confirm delete → track removed + toast | ✅ | Django messages framework |
| Toggle Public/Private | ✅ | |
| Share URL copied from library | ✅ | Share URL shown inline |
| Sorting / Filtering by genre (A2) | ✅ | Filter bar: search, genre, mood — GET params, icontains |
| Empty library friendly message (A3) | ✅ | CTA button to Generate |
| Playback failure error (E1) | ✅ | `audio.onerror` → toast in mini-player JS |
| Deletion DB error handling (E2) | ✅ | try/except in `delete_track_view` → `messages.error` |
| Skip / Previous track buttons (REQ-4.5.1) | ✅ | ⏮/⏭ buttons in mini-player; library embeds playlist in localStorage; auto-advance on track end |

### UC-03 — Admin Token Management

| Step | Status | Notes |
|------|--------|-------|
| Admin logs into `/admin/` | ✅ | Django Admin |
| Search user by name/email | ✅ | Admin search bar |
| View current token balance | ✅ | Inline on Profile |
| Set new token balance | ✅ | Validated 0–9999 |
| Change recorded in admin log | ✅ | `django_admin_log` (automatic) |
| Negative balance blocked (E1) | ✅ | `MinValueValidator(0)` |
| Bulk promotional grant (A1) | ✅ | `grant_tokens_action` custom Admin Action with intermediate form |

---

## 6. File Map

```
ai_music_generator/
├── settings.py          — all config (allauth, django-q2, API keys, auth backends)
├── urls.py              — root router (allauth.urls replaces auth.urls)
├── wsgi.py / asgi.py

music/
├── models/
│   ├── __init__.py
│   ├── user.py          — User entity (Creator/Admin role)
│   ├── profile.py       — Profile (token_balance)
│   ├── token_record.py  — Token audit trail
│   ├── library.py       — Library (1:1 User)
│   ├── folder.py        — Folder (N:1 Library)
│   └── song.py          — Song (core entity + created_at, updated_at)
├── controllers/
│   ├── __init__.py
│   ├── generate_music.py — UC-01 logic
│   ├── manage_library.py — UC-02 logic
│   └── admin_token.py    — UC-03 logic
├── services/
│   ├── __init__.py       — Provider registry + get_strategy()
│   ├── base.py           — Abstract MusicGenerationStrategy
│   ├── mureka.py         — Mureka API (~45 s)
│   └── suno.py           — Suno API (~30–60 s)
├── migrations/
│   ├── 0001_initial.py
│   ├── 0002_song_file_url.py
│   ├── 0003_song_provider.py
│   └── 0004_song_timestamps.py  ← added created_at, updated_at
├── management/commands/
│   └── seed_and_demo.py
├── tasks.py              — django-q2 background task (generate_music_task)
├── profanity.py          — Bad-word filter (REQ-5.2.1)
├── views.py              — All view functions + status API endpoint
├── urls.py               — App URL patterns (incl. /api/generation-status/)
├── admin.py              — Django Admin for all 6 models
└── templates/music/
    ├── base.html         — Shared layout with ALL frontend features
    ├── generate.html     — UC-01 generation form
    ├── library.html      — UC-02 track list
    └── public_listen.html — Public share page

templates/
└── registration/
    └── login.html        — Login page (username/password + Google OAuth button)

.env.example              — Template for all required environment variables
requirements.txt          — All Python dependencies
context_and_check_list.md — This file
```

---

## 7. Known Gaps / Future Work

| Item | SRS Ref | Priority | Status |
|------|---------|---------|--------|
| Unit tests for controllers and views | — | Medium | ❌ Not done |
| Folder management UI (model exists, no views) | Phase 2 (SRS App. C) | Low | ❌ Phase 2 |
| Pagination for large libraries | — | — | ✅ Done (20/page) |
| WAV/FLAC format selection on download | REQ-4.3.6, UC-01 A3 | Medium | ✅ Done |
| Skip / Previous track buttons in mini-player | REQ-4.5.1 | Medium | ✅ Done |
| Timeout aligned to SRS (20 min) | §5.1.2, UC-01 E3 | Low | ✅ Done (1200 s) |
| "Queued for generation…" status state | UC-01 E4 | Low | ✅ Done |
| IE11 "Browser Not Supported" blocking modal | SRS 5.6.2 | Low | ✅ Done |
| In-app browser "Open in External Browser" prompt | SRS 5.6.2 | Low | ✅ Done |
| Inline parameter tooltips on generate form | SRS §2.6 | Low | ✅ Done |
| Accessible font units (rem/em) | SRS §3.1.4 | Low | ✅ Done |

---

## 8. Setup Checklist (New Developer)

- [ ] Clone repo and create a virtual environment
- [ ] `pip install -r requirements.txt`
- [ ] Copy `.env.example` → `.env` and fill in all values
- [ ] `python manage.py migrate`
- [ ] `python manage.py createsuperuser`
- [ ] *(Optional)* Set up Google OAuth credentials and configure in Django Admin (see `.env.example`)
- [ ] Terminal 1: `python manage.py runserver`
- [ ] Terminal 2: `python manage.py qcluster`
- [ ] Open `http://127.0.0.1:8000/` and log in
- [ ] *(Optional)* `python manage.py seed_and_demo` to load sample data
