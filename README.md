# AI Music Generator Web App

A Django web application that allows users to generate, manage, and share AI-created music tracks using third-party music generation APIs (Suno / Mureka).

Prepared by **Chachalit Khanarat** — Hong Software Co.
Based on SRS v1.0 (29/01/2026)

---

## Quick Start

```bash
# 1. Create & activate a virtual environment
python -m venv venv
source venv/bin/activate     # Linux/Mac
venv\Scripts\activate        # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment config and fill in your values
cp .env.example .env

# 4. Apply database migrations
python manage.py migrate

# 5. Create a superuser (for Django Admin & local login)
python manage.py createsuperuser

# 6. Start the development server  (Terminal 1)
python manage.py runserver

# 7. Start the background task worker  (Terminal 2 — REQUIRED for music generation)
python manage.py qcluster
```

> **Both terminals must be running.** Without `qcluster`, submitted generation requests will queue in the database but never execute.

Visit `http://127.0.0.1:8000/` — you will be redirected to the login page.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID (see `.env.example` for setup steps) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `MUSIC_API_PROVIDER` | Default provider: `mureka` or `suno` |
| `MUREKA_API_KEY` | API key from platform.mureka.ai |
| `SUNO_API_KEY` | API key from sunoapi.org |
| `SUNO_BASE_URL` | Suno base URL (default: `https://api.sunoapi.org`) |

---

## Google OAuth Setup (one-time)

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials
2. Create an **OAuth 2.0 Client ID** (Web application)
3. Add authorised redirect URI: `http://localhost:8000/accounts/google/login/callback/`
4. Copy the Client ID and Secret into `.env`
5. In Django Admin → **Sites** → change domain to `localhost:8000`
6. In Django Admin → **Social Applications** → add a new Google provider using those credentials

---

## Features

| Feature | SRS Ref | Status |
|---------|---------|--------|
| Walled Garden (login required everywhere) | REQ-4.1.1 | ✅ |
| Username / password login | REQ-4.1.2 | ✅ |
| Google OAuth login | REQ-4.1.2 | ✅ |
| Token deduction per generation | REQ-4.2.1 | ✅ |
| Block generation when tokens = 0 | REQ-4.2.2 | ✅ |
| Admin token management (Django Admin) | REQ-4.2.3 | ✅ |
| 6-field music generation form | REQ-4.3.1 | ✅ |
| Async generation (non-blocking browser) | REQ-4.3.2 | ✅ |
| Navigate away while generating | REQ-4.3.3 | ✅ |
| Global status bar with real-time progress | REQ-4.3.4 | ✅ |
| Token refund on failure / timeout | REQ-4.3.7 | ✅ |
| Personal library with track list | REQ-4.4.1 | ✅ |
| Delete track (with confirmation modal) | REQ-4.4.2 | ✅ |
| Tracks private by default | REQ-4.4.3 | ✅ |
| Toggle public / private + share URL | REQ-4.4.4 | ✅ |
| Public Listen Page (no login required) | REQ-4.4.5 | ✅ |
| Persistent mini-player (Play, Pause, Seek, Volume) | REQ-4.5.1 | ✅ |
| Player continues across page navigation | REQ-4.5.2 | ✅ |
| Profanity / bad-word filter on inputs | REQ-5.2.1 | ✅ |
| API keys stored in environment variables | REQ-5.3.2 | ✅ |
| Dark / Light mode toggle | SRS 3.1.2 | ✅ |
| Responsive layout (320 px → desktop) | SRS 5.6.3 | ✅ |
| Toast notifications | UC-02 | ✅ |
| Empty library state with CTA | UC-02 A3 | ✅ |
| Generation / Failed status badges | UC-01 | ✅ |

---

## Architecture

```
ai_music_generator/          # Django project config
  settings.py                # All settings (allauth, django-q2, API keys)
  urls.py                    # Root router → allauth + music app

music/
  models/                    # Domain entities (1 file per model)
    user.py                  # User (Creator / Admin role)
    profile.py               # Profile (token_balance)
    token_record.py          # Token audit trail
    library.py               # Library (1-to-1 with User)
    folder.py                # Folder inside a Library
    song.py                  # Song (core entity, all metadata + timestamps)
  controllers/               # Use-case business logic
    generate_music.py        # UC-01: request, complete, fail, refund
    manage_library.py        # UC-02: list, delete, toggle privacy
    admin_token.py           # UC-03: set balance, list users
  services/                  # Strategy pattern for AI providers
    base.py                  # Abstract MusicGenerationStrategy
    mureka.py                # Mureka API implementation
    suno.py                  # Suno API implementation
    __init__.py              # Provider registry + get_strategy()
  tasks.py                   # django-q2 background task (async generation)
  profanity.py               # Bad-word filter (REQ-5.2.1)
  views.py                   # Django view functions
  urls.py                    # App URL patterns
  admin.py                   # Django Admin config for all models
  templates/music/
    base.html                # Shared layout: nav, status bar, mini-player,
                             #   theme toggle, toasts, modal, responsive CSS
    generate.html            # UC-01 generation form
    library.html             # UC-02 track list with play/delete/privacy actions
    public_listen.html       # Public share page (no auth required)
  migrations/                # 4 migration files (0001–0004)
  management/commands/
    seed_and_demo.py         # Demo seed data for all 3 use cases

templates/
  registration/login.html    # Login page with username + Google OAuth button
```

---

## Domain Model

| Entity | Key Fields |
|--------|-----------|
| **User** | name, email, role (Creator/Admin) |
| **Profile** | token_balance (integer, 0–9999) |
| **TokenRecord** | amount, type (Earned/Spent) |
| **Library** | one-to-one with User |
| **Folder** | name, FK → Library |
| **Song** | title, genre, mood, occasion, singer_style, topic, duration, status, provider, file_url, is_public, share_token, created_at, updated_at |

Song statuses: `Draft → Generating → Completed / Failed`

---

## Use Cases

### UC-01 — Generate and Share Music
1. User fills in the generation form (title required; genre, mood, occasion, singer style, topic optional)
2. System checks token balance and runs profanity filter
3. Tokens deducted; background task queued via django-q2
4. User is redirected to Library immediately (non-blocking)
5. Global status bar polls `/api/generation-status/` every 3 seconds and updates in real time
6. On completion the track appears in the Library; on failure tokens are refunded
7. User can toggle a track Public to get a shareable link; anyone can open it without logging in

### UC-02 — Manage Library & Playback
1. Library lists all tracks with status badges, genre, mood, duration, privacy
2. Click **Play** on a completed track → mini-player appears in the footer
3. Navigate to another page → audio keeps playing (state saved in localStorage)
4. Click **Delete** → confirmation modal; on confirm, track is removed and a toast appears
5. Click **Make Public / Private** → privacy toggled instantly
6. Empty library shows a friendly message with a link to the generator

### UC-03 — Admin Token Management
- Django Admin at `/admin/` → User Profiles → edit `token_balance`
- Every change is recorded in `django_admin_log` automatically
- Balance is validated: 0 ≤ balance ≤ 9999

---

## Running Tests

```bash
python manage.py test
```

> Test suite is a placeholder (`music/tests.py`). Unit tests for controllers and views are a planned next step.

---

## Seed Data (Demo)

```bash
python manage.py seed_and_demo
```

Creates sample users, profiles, libraries, and songs and prints a walkthrough of all three use cases.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `django>=5.0` | Web framework |
| `python-dotenv` | Load `.env` into settings |
| `requests` | HTTP calls to Suno / Mureka APIs |
| `django-allauth` | Google OAuth + account management |
| `django-q2` | Background task queue (async generation) |
| `PyJWT` | JWT verification for allauth Google provider |
| `cryptography` | Cryptographic backend for PyJWT |
