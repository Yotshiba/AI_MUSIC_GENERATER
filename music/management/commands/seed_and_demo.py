"""Management command that seeds sample data and demonstrates CRUD operations."""

from django.core.management.base import BaseCommand

from music.models import Folder, Library, Profile, Song, TokenRecord, User


class Command(BaseCommand):
    help = 'Seeds sample domain data and demonstrates CRUD operations'

    def handle(self, *args, **options):
        self.stdout.write('\n=== CREATE ===')

        # Create Users
        alice = User.objects.create(name='Alice', email='alice@example.com', role=User.UserRole.CREATOR)
        bob = User.objects.create(name='Bob', email='bob@example.com', role=User.UserRole.ADMIN)
        self.stdout.write(f'Created users: {alice}, {bob}')

        # Create Profiles (1:1)
        profile_a = Profile.objects.create(user=alice, token_balance=100)
        profile_b = Profile.objects.create(user=bob, token_balance=50)
        self.stdout.write(f'Created profiles: {profile_a}, {profile_b}')

        # Create Token Records (many per user)
        tr1 = TokenRecord.objects.create(user=alice, amount=100, type=TokenRecord.TokenType.EARNED)
        tr2 = TokenRecord.objects.create(user=alice, amount=20, type=TokenRecord.TokenType.SPENT)
        self.stdout.write(f'Created token records: {tr1}, {tr2}')

        # Create Libraries (1:1)
        lib_a = Library.objects.create(user=alice)
        lib_b = Library.objects.create(user=bob)
        self.stdout.write(f'Created libraries: {lib_a}, {lib_b}')

        # Create Folders
        pop_folder = Folder.objects.create(library=lib_a, name='Pop Songs')
        rock_folder = Folder.objects.create(library=lib_a, name='Rock Songs')
        self.stdout.write(f'Created folders: {pop_folder}, {rock_folder}')

        # Create Songs
        song1 = Song.objects.create(
            user=alice,
            folder=pop_folder,
            title='Sunshine Melody',
            genre='Pop',
            mood='Happy',
            occasion='Birthday',
            singer_style='Female Vocal',
            topic='Celebration',
            duration=210,
            status=Song.SongStatus.COMPLETED,
            is_public=True,
        )
        song2 = Song.objects.create(
            user=alice,
            folder=rock_folder,
            title='Thunder Road',
            genre='Rock',
            mood='Energetic',
            occasion='Road Trip',
            singer_style='Male Vocal',
            topic='Adventure',
            duration=240,
            status=Song.SongStatus.DRAFT,
        )
        song3 = Song.objects.create(
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
        all_users = User.objects.all()
        self.stdout.write(f'All users: {list(all_users.values_list("name", flat=True))}')

        alice_songs = Song.objects.filter(user=alice)
        self.stdout.write(f"Alice's songs: {list(alice_songs.values_list('title', flat=True))}")

        alice_profile = Profile.objects.get(user=alice)
        self.stdout.write(f"Alice's token balance: {alice_profile.token_balance}")

        alice_records = TokenRecord.objects.filter(user=alice)
        self.stdout.write(f"Alice's token records: {list(alice_records.values('amount', 'type'))}")

        folders = Folder.objects.filter(library=lib_a)
        self.stdout.write(f"Alice's folders: {list(folders.values_list('name', flat=True))}")

        # === UPDATE ===
        self.stdout.write('\n=== UPDATE ===')
        song2.status = Song.SongStatus.COMPLETED
        song2.is_public = True
        song2.save()
        self.stdout.write(f'Updated "{song2.title}" status to {song2.status}, is_public={song2.is_public}')

        alice_profile.token_balance -= 20
        alice_profile.save()
        self.stdout.write(f"Updated Alice's token balance to {alice_profile.token_balance}")

        pop_folder.name = 'Favourite Pop'
        pop_folder.save()
        self.stdout.write(f'Renamed folder to "{pop_folder.name}"')

        # === DELETE ===
        self.stdout.write('\n=== DELETE ===')
        song3_title = song3.title
        song3.delete()
        self.stdout.write(f'Deleted song: {song3_title}')

        remaining = Song.objects.count()
        self.stdout.write(f'Remaining songs: {remaining}')

        self.stdout.write(self.style.SUCCESS('\nCRUD demo completed successfully!'))
