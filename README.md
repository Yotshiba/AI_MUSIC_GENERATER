# AI Music Generator Web App

A Django web application that allows users to generate, manage, and share AI-created music tracks using third-party music generation APIs (Suno / Mureka).

Prepared by **Chachalit Khanarat** — Hong Software Co.
Based on SRS v1.0 (29/01/2026)

---

## 1. Installation

### Prerequisites
- Python 3.10+
- Git

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/Yotshiba/AI_MUSIC_GENERATER.git
cd AI_MUSIC_GENERATER

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables  (see Section 2 below)
cp .env.example .env
# → open .env and fill in your values

# 5. Apply database migrations
python manage.py migrate

# 6. Create a superuser (for Django Admin)
python manage.py createsuperuser
```

---

## 2. Environment Variables (Secret Keys)

All secrets are stored in a `.env` file at the project root. **Never commit this file.**
Copy the template and fill in your values:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ Always | Django secret key — generate one at [djecrety.ir](https://djecrety.ir) |
| `GENERATOR_STRATEGY` | ✅ Always | `mock` (offline) · `suno` · `mureka` · *(empty = user picks in form)* |
| `SUNO_API_KEY` | Suno mode only | API key from [sunoapi.org](https://sunoapi.org) |
| `SUNO_BASE_URL` | Suno mode only | Default: `https://api.sunoapi.org` |
| `MUREKA_API_KEY` | Mureka mode only | API key from [platform.mureka.ai](https://platform.mureka.ai) |
| `MUSIC_API_PROVIDER` | Optional | Default provider shown in the form: `mureka` or `suno` |
| `GOOGLE_CLIENT_ID` | OAuth only | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth only | Google OAuth client secret |

### How to get a Suno API key

1. Go to [sunoapi.org](https://sunoapi.org) and create an account
2. Navigate to **API Keys** in your dashboard
3. Click **Create Key** and copy the key
4. Paste it into `.env`:
   ```
   SUNO_API_KEY=sk-...your-key-here...
   SUNO_BASE_URL=https://api.sunoapi.org
   GENERATOR_STRATEGY=suno
   ```

### How to get a Mureka API key

1. Go to [platform.mureka.ai](https://platform.mureka.ai) and create an account
2. Go to **API Keys** → **Create**
3. Copy the key and paste into `.env`:
   ```
   MUREKA_API_KEY=your-mureka-key-here
   GENERATOR_STRATEGY=mureka
   ```

### Google OAuth setup (optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials
2. Create an **OAuth 2.0 Client ID** (Web application)
3. Add authorised redirect URI: `http://localhost:8000/accounts/google/login/callback/`
4. Paste the Client ID and Secret into `.env`
5. In Django Admin → **Sites** → set domain to `localhost:8000`
6. In Django Admin → **Social Applications** → add Google provider with those credentials

---

## 3. Running the App

> ⚠️ **Two terminals are required.** The web server and the background task worker must both be running for music generation to work.

### Mode A — Mock Mode (offline, no API key needed)

Use this for development and testing. Generation returns a fixed sample MP3 in ~2 seconds with no external API calls.

**Step 1** — set in `.env`:
```
GENERATOR_STRATEGY=mock
```

**Step 2** — start the servers:
```bash
# Terminal 1 — web server
python manage.py runserver

# Terminal 2 — background worker (required for generation)
python manage.py qcluster
```

**Step 3** — open `http://127.0.0.1:8000/`, log in, submit the generation form.
The status bar will show **"Ready!"** in ~2 seconds and a placeholder MP3 will appear in your library.

---

### Mode B — Suno Mode (real AI generation)

**Step 1** — set in `.env`:
```
GENERATOR_STRATEGY=suno
SUNO_API_KEY=sk-...your-key-here...
SUNO_BASE_URL=https://api.sunoapi.org
```

**Step 2** — start the servers:
```bash
# Terminal 1
python manage.py runserver

# Terminal 2
python manage.py qcluster
```

**Step 3** — open `http://127.0.0.1:8000/`, log in, submit the generation form.
The Suno strategy will:
1. POST to `/api/v1/generate` with your Bearer token
2. Extract the returned `taskId`
3. Poll `GET /api/v1/generate/record-info?taskId=...` every 5 seconds
4. Return the audio URL when status reaches `SUCCESS` or `FIRST_SUCCESS`

Generation typically completes in **30–60 seconds**. The status bar updates in real time.

---

### Mode C — Mureka Mode

**Step 1** — set in `.env`:
```
GENERATOR_STRATEGY=mureka
MUREKA_API_KEY=your-mureka-key-here
```

**Step 2** — start both servers (same as above).

---

## 4. Demonstration — Example Run Output

Both strategies are covered by the automated test suite (20 tests). Run them with:

```bash
python manage.py test music.tests --verbosity=2
```

### Mock Strategy — evidence it works

```
test_mock_generate_returns_url (music.tests.MockStrategyTests.test_mock_generate_returns_url)
Mock generate() returns a non-empty audio URL without any network call. ... ok

test_mock_generate_no_network (music.tests.MockStrategyTests.test_mock_generate_no_network)
Mock generate() must NOT make any HTTP requests. ... ok

test_mock_generate_is_deterministic (music.tests.MockStrategyTests.test_mock_generate_is_deterministic)
Mock always returns the same URL regardless of song parameters. ... ok
```

The mock strategy returns a fixed public MP3 URL after a 2-second simulated delay — **no API key, no network required**:

```
audio_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
```

---

### Suno Strategy — evidence it creates a taskId and retrieves status

**Test: taskId is extracted and used for polling**
```
test_suno_creates_task_id_on_submit (music.tests.SunoStrategyTests.test_suno_creates_task_id_on_submit)
Verify Suno extracts and uses the taskId returned by the generate endpoint. ...
[DEBUG] music: poll_until taskId=task-unique-789 data={'status': 'SUCCESS',
  'response': {'sunoData': [{'streamAudioUrl': 'https://cdn.sunoapi.org/example.mp3',
                             'audioUrl':       'https://cdn.sunoapi.org/example.mp3'}]}}
ok
```

**Test: full happy-path flow (POST → taskId → poll → audio URL)**
```
test_suno_generate_full_flow (music.tests.SunoStrategyTests.test_suno_generate_full_flow)
Demonstrate Suno strategy full happy-path flow: ...
[DEBUG] music: poll_until taskId=task-demo-456 data={'status': 'SUCCESS',
  'response': {'sunoData': [{'streamAudioUrl': 'https://cdn.sunoapi.org/demo-track.mp3',
                             'audioUrl':       'https://cdn.sunoapi.org/demo-track.mp3'}]}}
ok
```

**Test: polling loops until status changes from PENDING → SUCCESS**
```
test_suno_polls_until_success (music.tests.SunoStrategyTests.test_suno_polls_until_success)
Verify Suno polls multiple times if status is not yet SUCCESS. ...
[DEBUG] music: poll_until taskId=task-111 data={'status': 'PENDING', 'response': {}}
[DEBUG] music: poll_until taskId=task-111 data={'status': 'PENDING', 'response': {}}
[DEBUG] music: poll_until taskId=task-111 data={'status': 'SUCCESS',
  'response': {'sunoData': [{'streamAudioUrl': 'https://cdn.sunoapi.org/example.mp3'}]}}
ok
```

**Test: failure status is detected and RuntimeError is raised**
```
test_suno_raises_on_failed_status (music.tests.SunoStrategyTests.test_suno_raises_on_failed_status)
Verify Suno raises RuntimeError when API returns FAILED status. ...
[DEBUG] music: poll_until taskId=task-fail data={'status': 'FAILED', 'response': {}}
[ERROR] music: Provider reported failure: taskId=task-fail data={'status': 'FAILED', 'response': {}}
ok
```

**Full test suite result:**
```
----------------------------------------------------------------------
Ran 20 tests in 0.008s

OK
```

---

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

## Exercise 4 — Strategy Pattern (Mock vs Suno API)

### Strategy Interface

Defined in `music/services/base.py`:

```python
class MusicGenerationStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def generate(self, song) -> str:
        """Submit parameters, poll until complete, return audio URL."""
```

### Available Strategies

| Key | Class | File | Description |
|-----|-------|------|-------------|
| `mock` | `MockSongGeneratorStrategy` | `music/services/mock.py` | Offline, deterministic — returns a fixed audio URL after a 2 s delay. No API key needed. |
| `suno` | `SunoStrategy` | `music/services/suno.py` | Calls `api.sunoapi.org` — POST to generate, polls `record-info` until `SUCCESS`. |
| `mureka` | `MurekaStrategy` | `music/services/mureka.py` | Calls `api.mureka.ai` — POST to generate, polls `song/query/{id}` until `complete`. |

Strategy selection is **centralized** in `music/services/__init__.py → get_strategy()`.

### Running in Mock Mode (offline, no API key)

→ See **[Section 3 — Mode A](#mode-a--mock-mode-offline-no-api-key-needed)** for full instructions.

Summary: set `GENERATOR_STRATEGY=mock` in `.env` — no API key required.

### Running in Suno Mode

→ See **[Section 3 — Mode B](#mode-b--suno-mode-real-ai-generation)** for full instructions.

Summary: set `GENERATOR_STRATEGY=suno` and `SUNO_API_KEY=sk-...` in `.env`.

The Suno strategy:
1. POSTs to `/api/v1/generate` with `Authorization: Bearer <token>`
2. Extracts the returned `taskId`
3. Polls `GET /api/v1/generate/record-info?taskId=...` every 5 seconds
4. Returns the `streamAudioUrl` once status is `SUCCESS` or `FIRST_SUCCESS`

### Where to put the Suno API key

**Never commit your key.** Store it only in `.env` (which is git-ignored):

```
SUNO_API_KEY=sk-...your-key-here...
```

Get your key from [sunoapi.org](https://sunoapi.org).

### Strategy Selection Logic

`GENERATOR_STRATEGY` in `.env` controls which provider is used globally:

```
GENERATOR_STRATEGY=mock    # All generation uses Mock (offline, no API key)
GENERATOR_STRATEGY=suno    # All generation uses Suno
GENERATOR_STRATEGY=mureka  # All generation uses Mureka
GENERATOR_STRATEGY=        # (empty) — user's form choice is used
```

---



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
    base.py                  # Abstract MusicGenerationStrategy (ABC)
    mock.py                  # Mock strategy (offline, deterministic)
    mureka.py                # Mureka API implementation
    suno.py                  # Suno API implementation
    utils.py                 # Shared poll_until() utility
    __init__.py              # Provider registry + get_strategy()
  signals.py                 # post_save signal: auto-create Profile + Library on User creation
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

## Class Diagram

The diagram is organized by the **MVT + Controller + Strategy** architecture layers. Each layer is colour-coded.

| Layer | Colour |
|-------|--------|
| 🟦 Model | Blue |
| 🟩 Controller | Green |
| 🟧 Service / Strategy | Orange |
| 🟥 View | Red |
| 🟪 Template | Purple |

---

## Sequence Diagrams

### UC-01 — Generate Music (Happy Path)

![UC-01 Happy Path Sequence Diagram](diagrams/UC01_Happy_Path.png)

### UC-01 — Generate Music (Failure / Timeout Path)

![UC-01 Failure Path Sequence Diagram](diagrams/UC01_Failure_Path.png)

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

The test suite covers the Strategy Pattern (20 tests):
- Strategy interface (ABC, inheritance, registry)
- Mock strategy (deterministic output, no network)
- Suno strategy (task submission, polling, failure handling)
- Strategy selection (env-var override, case-insensitive lookup)

All 20 tests pass.

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
