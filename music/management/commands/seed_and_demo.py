"""Management command that seeds sample data and demonstrates CRUD operations."""

from django.core.management.base import BaseCommand

from music.controllers import MusicController
from music.models import Folder, Library, Profile, Song, TokenRecord, User


class Command(BaseCommand):
    help = 'Seeds sample domain data and demonstrates CRUD operations'

    def handle(self, *args, **options):
        ctrl = MusicController

        # Clean previous seed data so the command is re-runnable
        Song.objects.all().delete()
        Folder.objects.all().delete()
        Library.objects.all().delete()
        TokenRecord.objects.all().delete()
        Profile.objects.all().delete()
        User.objects.all().delete()

        self.stdout.write('\n=== CREATE ===')

        # Create Users
        alice = ctrl.create_user(name='Alice', email='alice@example.com', role=User.UserRole.CREATOR)
        bob = ctrl.create_user(name='Bob', email='bob@example.com', role=User.UserRole.ADMIN)
        self.stdout.write(f'Created users: {alice}, {bob}')

        # Create Profiles (1:1)
        profile_a = ctrl.create_profile(user=alice, token_balance=100)
        profile_b = ctrl.create_profile(user=bob, token_balance=50)
        self.stdout.write(f'Created profiles: {profile_a}, {profile_b}')

        # Create Token Records (many per user)
        tr1 = ctrl.create_token_record(user=alice, amount=100, type=TokenRecord.TokenType.EARNED)
        tr2 = ctrl.create_token_record(user=alice, amount=20, type=TokenRecord.TokenType.SPENT)
        self.stdout.write(f'Created token records: {tr1}, {tr2}')

        # Create Libraries (1:1)
        lib_a = ctrl.create_library(user=alice)
        lib_b = ctrl.create_library(user=bob)
        self.stdout.write(f'Created libraries: {lib_a}, {lib_b}')

        # Create Folders
        pop_folder = ctrl.create_folder(library=lib_a, name='Pop Songs')
        rock_folder = ctrl.create_folder(library=lib_a, name='Rock Songs')
        self.stdout.write(f'Created folders: {pop_folder}, {rock_folder}')

        # Create Songs
        song1 = ctrl.create_song(
            user=alice,
            title='Sunshine Melody',
            folder=pop_folder,
            genre='Pop',
            mood='Happy',
            occasion='Birthday',
            singer_style='Female Vocal',
            topic='Celebration',
            duration=210,
            status=Song.SongStatus.COMPLETED,
            is_public=True,
        )
        song2 = ctrl.create_song(
            user=alice,
            title='Thunder Road',
            folder=rock_folder,
            genre='Rock',
            mood='Energetic',
            occasion='Road Trip',
            singer_style='Male Vocal',
            topic='Adventure',
            duration=240,
            status=Song.SongStatus.DRAFT,
        )
        song3 = ctrl.create_song(
            user=bob,
            title='Night Jazz',
            genre='Jazz',
            mood='Relaxed',
            duration=180,
            status=Song.SongStatus.GENERATING,
        )
        self.stdout.write(f'Created songs: {song1}, {song2}, {song3}')

        # === READ ===
        self.stdout.write('\n=== READ ===')
        all_users = ctrl.list_users()
        self.stdout.write(f'All users: {list(all_users.values_list("name", flat=True))}')

        alice_songs = ctrl.list_songs(user=alice)
        self.stdout.write(f"Alice's songs: {list(alice_songs.values_list('title', flat=True))}")

        alice_profile = ctrl.get_profile(user_id=alice.pk)
        self.stdout.write(f"Alice's token balance: {alice_profile.token_balance}")

        alice_records = ctrl.list_token_records(user_id=alice.pk)
        self.stdout.write(f"Alice's token records: {list(alice_records.values('amount', 'type'))}")

        folders = ctrl.list_folders(library_id=lib_a.pk)
        self.stdout.write(f"Alice's folders: {list(folders.values_list('name', flat=True))}")

        # === UPDATE ===
        self.stdout.write('\n=== UPDATE ===')
        song2 = ctrl.update_song(song2.pk, status=Song.SongStatus.COMPLETED, is_public=True)
        self.stdout.write(f'Updated "{song2.title}" status to {song2.status}, is_public={song2.is_public}')

        alice_profile = ctrl.update_profile(user_id=alice.pk, token_balance=80)
        self.stdout.write(f"Updated Alice's token balance to {alice_profile.token_balance}")

        pop_folder = ctrl.update_folder(pop_folder.pk, name='Favourite Pop')
        self.stdout.write(f'Renamed folder to "{pop_folder.name}"')

        # === DELETE ===
        self.stdout.write('\n=== DELETE ===')
        song3_title = song3.title
        ctrl.delete_song(song3.pk)
        self.stdout.write(f'Deleted song: {song3_title}')

        remaining = Song.objects.count()
        self.stdout.write(f'Remaining songs: {remaining}')

        self.stdout.write(self.style.SUCCESS('\nCRUD demo completed successfully!'))
