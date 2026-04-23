from django.apps import AppConfig


class MusicConfig(AppConfig):
    name = 'music'

    def ready(self):
        import music.signals  # noqa: F401 — registers post_save signal
