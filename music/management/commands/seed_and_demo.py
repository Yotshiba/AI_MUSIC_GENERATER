"""Management command that seeds sample data and demonstrates the three use case flows."""

from django.core.management.base import BaseCommand

from music.controllers import (
    AdminTokenController,
    GenerateMusicController,
    InsufficientTokensError,
    ManageLibraryController,
)
from music.models import Folder, Library, Profile, Song, TokenRecord, User


class Command(BaseCommand):
    help = 'Seeds sample domain data and demonstrates the three SRS use case flows'

    def handle(self, *args, **options):
        # ── Clean previous seed data so the command is re-runnable ──────────
        Song.objects.all().delete()
        Folder.objects.all().delete()
        Library.objects.all().delete()
        TokenRecord.objects.all().delete()
        Profile.objects.all().delete()
        User.objects.all().delete()

        # ── Setup (registration scaffolding — not a use case) ────────────────
        self.stdout.write('\n=== SETUP ===')
        bella = User.objects.create(name='Bella', email='bella@example.com', role=User.UserRole.CREATOR)
        admin_alex = User.objects.create(name='Alex', email='alex@example.com', role=User.UserRole.ADMIN)
        Profile.objects.create(user=bella, token_balance=5)
        Profile.objects.create(user=admin_alex, token_balance=0)
        Library.objects.create(user=bella)
        Library.objects.create(user=admin_alex)
        self.stdout.write(f'Created users: {bella} (5 tokens), {admin_alex} (admin)')

        # ────────────────────────────────────────────────────────────────────
        # UC-01: Generate and Share Brand-Safe Background Music
        # ────────────────────────────────────────────────────────────────────
        self.stdout.write('\n=== UC-01: Generate and Share Music ===')

        # Happy path — sufficient tokens
        song = GenerateMusicController.request_generation(
            user=bella,
            title='Sukhumvit Rain',
            genre='Lo-Fi / Chill-hop',
            mood='Melancholic but cozy',
            occasion='Vlog Background',
            singer_style='Instrumental',
            topic='Rainy afternoon coffee shop',
        )
        self.stdout.write(f'Requested generation: "{song.title}" (status={song.status})')

        bella_profile = Profile.objects.get(user=bella)
        self.stdout.write(f"Bella's token balance after deduction: {bella_profile.token_balance}")

        # Background task completes successfully
        song = GenerateMusicController.mark_complete(song.pk)
        self.stdout.write(f'Generation complete: "{song.title}" (status={song.status})')

        # Share the track — toggle from Private to Public
        song = ManageLibraryController.toggle_privacy(song.pk, user=bella)
        self.stdout.write(f'Toggled privacy: is_public={song.is_public}, share_token={song.share_token}')

        # Public Listener accesses via share token (no login required)
        public_song = GenerateMusicController.get_public_track(share_token=song.share_token)
        self.stdout.write(f'Public track retrieved: "{public_song.title}"')

        # Exception flow — insufficient tokens (Bella now has 4 tokens, request a 2nd song)
        song2 = GenerateMusicController.request_generation(
            user=bella, title='Bangkok Rush', genre='Rock', mood='Energetic',
        )
        song2 = GenerateMusicController.mark_failed(song2.pk)
        bella_profile.refresh_from_db()
        self.stdout.write(
            f'Failed generation: "{song2.title}" (status={song2.status}), '
            f'tokens refunded -> balance={bella_profile.token_balance}'
        )

        # Block: drain balance to 0 then attempt generation
        Profile.objects.filter(user=bella).update(token_balance=0)
        try:
            GenerateMusicController.request_generation(user=bella, title='No Tokens Song')
        except InsufficientTokensError as exc:
            self.stdout.write(f'Blocked (no tokens): {exc}')

        # ────────────────────────────────────────────────────────────────────
        # UC-02: Manage Personal Library & Playback
        # ────────────────────────────────────────────────────────────────────
        self.stdout.write('\n=== UC-02: Manage Personal Library ===')

        # Restore balance and generate a second track for the demo
        Profile.objects.filter(user=bella).update(token_balance=10)
        song3 = GenerateMusicController.request_generation(
            user=bella, title='Night Bloom', genre='Jazz', mood='Relaxed',
        )
        GenerateMusicController.mark_complete(song3.pk)

        tracks = ManageLibraryController.list_tracks(user=bella)
        self.stdout.write(f"Bella's library: {list(tracks.values_list('title', flat=True))}")

        # Toggle privacy on a track from the library view
        song3 = ManageLibraryController.toggle_privacy(song3.pk, user=bella)
        self.stdout.write(f'Toggled privacy on "{song3.title}": is_public={song3.is_public}')

        # Delete a track (ownership enforced)
        title_to_delete = song3.title
        ManageLibraryController.delete_track(song3.pk, user=bella)
        remaining = ManageLibraryController.list_tracks(user=bella)
        self.stdout.write(
            f'Deleted "{title_to_delete}". Remaining: {list(remaining.values_list("title", flat=True))}'
        )

        # ────────────────────────────────────────────────────────────────────
        # UC-03: Admin Token Management
        # ────────────────────────────────────────────────────────────────────
        self.stdout.write('\n=== UC-03: Admin Token Management ===')

        user, profile = AdminTokenController.get_user_profile(bella.pk)
        self.stdout.write(f'Admin viewing profile: {user.name}, token_balance={profile.token_balance}')

        # Refund 10 tokens (simulate failed generation support ticket)
        profile = AdminTokenController.set_token_balance(bella.pk, profile.token_balance + 10)
        self.stdout.write(f'Admin set token balance to {profile.token_balance}')

        # Exception flow — negative balance attempt
        try:
            AdminTokenController.set_token_balance(bella.pk, -50)
        except ValueError as exc:
            self.stdout.write(f'Blocked (negative balance): {exc}')

        # List users for admin dashboard
        users = AdminTokenController.list_users()
        self.stdout.write(f'All users: {list(users.values_list("name", flat=True))}')

        self.stdout.write(self.style.SUCCESS('\nAll three use case flows completed successfully!'))
