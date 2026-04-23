"""
Unit tests for Exercise 4 — Strategy Pattern (Mock vs Suno API).

Run with: python manage.py test music.tests
"""

from unittest.mock import MagicMock, call, patch

from django.test import TestCase

from music.services import AVAILABLE_PROVIDERS, get_strategy
from music.services.base import MusicGenerationStrategy
from music.services.mock import MockSongGeneratorStrategy
from music.services.mureka import MurekaStrategy
from music.services.suno import SunoStrategy


# ── Helpers ───────────────────────────────────────────────────────────────

def _make_song(title="Test Song", genre="Jazz", mood="Chill",
               occasion="Vlog", singer_style="Female", topic="Rain"):
    """Return a lightweight mock Song object (no DB required)."""
    song = MagicMock()
    song.title        = title
    song.genre        = genre
    song.mood         = mood
    song.occasion     = occasion
    song.singer_style = singer_style
    song.topic        = topic
    return song


# ── Strategy Interface Tests ──────────────────────────────────────────────

class StrategyInterfaceTests(TestCase):
    """Verify the Abstract Base Class contract is correctly defined."""

    def test_base_is_abstract(self):
        """MusicGenerationStrategy cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            MusicGenerationStrategy()

    def test_mock_inherits_base(self):
        self.assertTrue(issubclass(MockSongGeneratorStrategy, MusicGenerationStrategy))

    def test_suno_inherits_base(self):
        self.assertTrue(issubclass(SunoStrategy, MusicGenerationStrategy))

    def test_mureka_inherits_base(self):
        self.assertTrue(issubclass(MurekaStrategy, MusicGenerationStrategy))

    def test_all_providers_registered(self):
        self.assertIn('mock',   AVAILABLE_PROVIDERS)
        self.assertIn('suno',   AVAILABLE_PROVIDERS)
        self.assertIn('mureka', AVAILABLE_PROVIDERS)


# ── Strategy Selection Tests ──────────────────────────────────────────────

class StrategySelectionTests(TestCase):
    """Verify get_strategy() returns the correct concrete class."""

    def test_get_strategy_mock(self):
        strategy = get_strategy('mock')
        self.assertIsInstance(strategy, MockSongGeneratorStrategy)

    def test_get_strategy_suno(self):
        strategy = get_strategy('suno')
        self.assertIsInstance(strategy, SunoStrategy)

    def test_get_strategy_mureka(self):
        strategy = get_strategy('mureka')
        self.assertIsInstance(strategy, MurekaStrategy)

    def test_get_strategy_case_insensitive(self):
        self.assertIsInstance(get_strategy('MOCK'), MockSongGeneratorStrategy)
        self.assertIsInstance(get_strategy('Suno'), SunoStrategy)

    def test_get_strategy_unknown_raises(self):
        with self.assertRaises(ValueError):
            get_strategy('nonexistent_provider')

    def test_generator_strategy_override_env_var(self):
        """GENERATOR_STRATEGY setting forces mock even when 'suno' is requested."""
        from django.conf import settings
        original = getattr(settings, 'GENERATOR_STRATEGY', '')
        try:
            settings.GENERATOR_STRATEGY = 'mock'
            strategy = get_strategy('suno')
            self.assertIsInstance(strategy, MockSongGeneratorStrategy,
                msg="GENERATOR_STRATEGY=mock should override 'suno' provider request")
        finally:
            settings.GENERATOR_STRATEGY = original


# ── Strategy A: Mock Generator Tests ─────────────────────────────────────

class MockStrategyTests(TestCase):
    """
    Demonstrates Mock strategy works offline with no API calls.
    """

    def test_mock_name(self):
        strategy = MockSongGeneratorStrategy()
        self.assertEqual(strategy.name, 'Mock')

    @patch('music.services.mock.time.sleep', return_value=None)
    def test_mock_generate_returns_url(self, _sleep):
        """Mock generate() returns a non-empty audio URL without any network call."""
        strategy = MockSongGeneratorStrategy()
        song = _make_song()
        url = strategy.generate(song)
        self.assertIsInstance(url, str)
        self.assertTrue(url.startswith('http'),
            msg=f"Expected URL starting with 'http', got: {url!r}")

    @patch('music.services.mock.time.sleep', return_value=None)
    def test_mock_generate_is_deterministic(self, _sleep):
        """Mock always returns the same URL regardless of song parameters."""
        strategy = MockSongGeneratorStrategy()
        url1 = strategy.generate(_make_song(title="Song A", genre="Rock"))
        url2 = strategy.generate(_make_song(title="Song B", genre="Jazz"))
        self.assertEqual(url1, url2,
            msg="Mock strategy must be deterministic")

    @patch('music.services.mock.time.sleep', return_value=None)
    def test_mock_generate_no_network(self, _sleep):
        """Mock generate() must NOT make any HTTP requests."""
        strategy = MockSongGeneratorStrategy()
        song = _make_song()
        with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
            strategy.generate(song)
            mock_get.assert_not_called()
            mock_post.assert_not_called()


# ── Strategy B: Suno API Generator Tests ─────────────────────────────────

class SunoStrategyTests(TestCase):
    """
    Demonstrates Suno strategy integration flow (API calls mocked to avoid
    requiring a real API key in the test environment).

    Shows:
      1. POST to /api/v1/generate with Bearer token → receives taskId
      2. GET /api/v1/generate/record-info?taskId=... → polls for status
      3. Returns streamAudioUrl on SUCCESS
    """

    def _make_suno_generate_response(self, task_id="task-abc-123"):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "code": 200,
            "msg": "success",
            "data": {"taskId": task_id},
        }
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    def _make_suno_poll_response(self, status="SUCCESS",
                                  audio_url="https://cdn.sunoapi.org/example.mp3"):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "code": 200,
            "data": {
                "status": status,
                "response": {
                    "sunoData": [
                        {
                            "streamAudioUrl": audio_url,
                            "audioUrl": audio_url,
                        }
                    ]
                },
            },
        }
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    def test_suno_name(self):
        strategy = SunoStrategy()
        self.assertEqual(strategy.name, 'Suno')

    @patch('music.services.utils.time.sleep', return_value=None)
    @patch('music.services.suno.requests.get')
    @patch('music.services.suno.requests.post')
    def test_suno_generate_full_flow(self, mock_post, mock_get, mock_sleep):
        """
        Demonstrate Suno strategy full happy-path flow:
        POST to generate → get taskId → poll record-info → return audio URL.
        """
        task_id   = "task-demo-456"
        audio_url = "https://cdn.sunoapi.org/demo-track.mp3"

        mock_post.return_value = self._make_suno_generate_response(task_id)
        mock_get.return_value  = self._make_suno_poll_response("SUCCESS", audio_url)

        from django.conf import settings
        settings.SUNO_API_KEY  = "test-api-key"
        settings.SUNO_BASE_URL = "https://api.sunoapi.org"

        strategy = SunoStrategy()
        result   = strategy.generate(_make_song())

        # 1. Verify POST was called with correct endpoint and Bearer token
        mock_post.assert_called_once()
        post_args, post_kwargs = mock_post.call_args
        self.assertIn('/api/v1/generate', post_args[0])
        self.assertEqual(post_kwargs['headers']['Authorization'], 'Bearer test-api-key')

        # 2. Verify POST body included prompt and callBackUrl
        self.assertIn('prompt', post_kwargs['json'])

        # 3. Verify GET was called with correct record-info endpoint + taskId
        mock_get.assert_called()
        get_args, get_kwargs = mock_get.call_args
        self.assertIn('record-info', get_args[0])
        self.assertEqual(get_kwargs['params']['taskId'], task_id)

        # 4. Verify final result is the audio URL
        self.assertEqual(result, audio_url)

    @patch('music.services.utils.time.sleep', return_value=None)
    @patch('music.services.suno.requests.get')
    @patch('music.services.suno.requests.post')
    def test_suno_creates_task_id_on_submit(self, mock_post, mock_get, mock_sleep):
        """Verify Suno extracts and uses the taskId returned by the generate endpoint."""
        task_id = "task-unique-789"
        mock_post.return_value = self._make_suno_generate_response(task_id)
        mock_get.return_value  = self._make_suno_poll_response("SUCCESS")

        from django.conf import settings
        settings.SUNO_API_KEY  = "test-key"
        settings.SUNO_BASE_URL = "https://api.sunoapi.org"

        strategy = SunoStrategy()
        strategy.generate(_make_song())

        # The GET poll must use the taskId returned from the POST
        get_args, get_kwargs = mock_get.call_args
        self.assertEqual(get_kwargs['params']['taskId'], task_id,
            msg=f"Suno must pass the taskId ({task_id!r}) when polling record-info")

    @patch('music.services.utils.time.sleep', return_value=None)
    @patch('music.services.suno.requests.get')
    @patch('music.services.suno.requests.post')
    def test_suno_polls_until_success(self, mock_post, mock_get, mock_sleep):
        """Verify Suno polls multiple times if status is not yet SUCCESS."""
        mock_post.return_value = self._make_suno_generate_response("task-111")

        pending_resp = self._make_suno_poll_response("PENDING")
        pending_resp.json.return_value = {
            "code": 200,
            "data": {"status": "PENDING", "response": {}},
        }
        success_resp = self._make_suno_poll_response("SUCCESS")

        # First two polls return PENDING, third returns SUCCESS
        mock_get.side_effect = [pending_resp, pending_resp, success_resp]

        from django.conf import settings
        settings.SUNO_API_KEY  = "test-key"
        settings.SUNO_BASE_URL = "https://api.sunoapi.org"

        strategy = SunoStrategy()
        strategy.generate(_make_song())

        self.assertEqual(mock_get.call_count, 3,
            msg="Suno should poll exactly 3 times: 2 PENDING + 1 SUCCESS")

    @patch('music.services.utils.time.sleep', return_value=None)
    @patch('music.services.suno.requests.get')
    @patch('music.services.suno.requests.post')
    def test_suno_raises_on_failed_status(self, mock_post, mock_get, mock_sleep):
        """Verify Suno raises RuntimeError when API returns FAILED status."""
        mock_post.return_value = self._make_suno_generate_response("task-fail")
        failed_resp = MagicMock()
        failed_resp.raise_for_status = MagicMock()
        failed_resp.json.return_value = {
            "code": 200,
            "data": {"status": "FAILED", "response": {}},
        }
        mock_get.return_value = failed_resp

        from django.conf import settings
        settings.SUNO_API_KEY  = "test-key"
        settings.SUNO_BASE_URL = "https://api.sunoapi.org"

        strategy = SunoStrategy()
        with self.assertRaises(RuntimeError):
            strategy.generate(_make_song())

