# AI Music Generator – Domain Layer (Exercise 3)

Django implementation of the AI Music Generator domain model.

## Domain Entities

| Entity | Description |
|---|---|
| **User** | A platform user with a role (Creator / Admin) |
| **Profile** | One-to-one with User; holds `token_balance` |
| **TokenRecord** | Many-per-user record of token transactions (Earned / Spent) |
| **Library** | One-to-one with User; organises songs into folders |
| **Folder** | Named folder inside a Library; holds songs |
| **Song** | Core entity with title, genre, mood, occasion, singer style, topic, duration, status (Draft / Generating / Completed / Failed), visibility flag, and share token |

## Setup

```bash
# 1. Create & activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations
python manage.py migrate

# 4. Create a superuser for Django Admin
python manage.py createsuperuser

# 5. Run the development server
python manage.py runserver
```

## CRUD Operations

### Via Django Admin

Visit `http://127.0.0.1:8000/admin/` and log in with your superuser credentials.
All domain entities (User, Profile, TokenRecord, Library, Folder, Song) are registered and fully manageable through the admin interface.

### Via Management Command

Run the included demo command to seed sample data and see Create, Read, Update, and Delete operations in action:

```bash
python manage.py seed_and_demo
```

Output demonstrates:
- **Create** – Users, Profiles, TokenRecords, Libraries, Folders, Songs
- **Read** – Querying users, filtering songs by user, retrieving token balances
- **Update** – Changing song status, adjusting token balance, renaming folders
- **Delete** – Removing a song and verifying the count

### Via MusicController

All CRUD operations are handled by a single unified controller (`music/controllers.py`):

```python
from music.controllers import MusicController

# Create
user = MusicController.create_user(name='Alice', email='alice@example.com')
profile = MusicController.create_profile(user=user, token_balance=100)
library = MusicController.create_library(user=user)
folder = MusicController.create_folder(library=library, name='My Songs')
song = MusicController.create_song(user=user, title='My Song', genre='Pop')

# Read
user = MusicController.get_user(user_id=1)
songs = MusicController.list_songs(user=user)

# Update
MusicController.update_song(song_id=1, status='Completed', is_public=True)

# Delete
MusicController.delete_song(song_id=1)
```

## Project Structure

```
ai_music_generator/          # Django project settings
music/
  models/                    # Domain models (1 model per file)
    __init__.py              # Re-exports all models
    user.py                  # User model
    profile.py               # Profile model
    token_record.py          # TokenRecord model
    library.py               # Library model
    folder.py                # Folder model
    song.py                  # Song model
  controllers.py             # Unified MusicController with CRUD for all models
  admin.py                   # Django Admin registration for CRUD
  management/commands/
    seed_and_demo.py         # Management command demonstrating CRUD operations
  migrations/                # Database migration files
```

## Class Diagram

```mermaid
classDiagram
    class UserRole {
        <<enumeration>>
        Creator
        Admin
    }

    class SongStatus {
        <<enumeration>>
        Draft
        Generating
        Completed
        Failed
    }

    class TokenType {
        <<enumeration>>
        Earned
        Spent
    }

    class User {
        +String name
        +String email
        +UserRole role
        +__str__() String
    }

    class Profile {
        +Integer token_balance
        +__str__() String
    }

    class TokenRecord {
        +Integer amount
        +TokenType type
        +__str__() String
    }

    class Library {
        +__str__() String
    }

    class Folder {
        +String name
        +__str__() String
    }

    class Song {
        +String title
        +String genre
        +String mood
        +String occasion
        +String singer_style
        +String topic
        +Integer duration
        +SongStatus status
        +Boolean is_public
        +UUID share_token
        +__str__() String
    }

    class MusicController {
        +create_user(name, email, role)$ User
        +get_user(user_id)$ User
        +list_users(filters)$ QuerySet
        +update_user(user_id, kwargs)$ User
        +delete_user(user_id)$ void
        +create_profile(user, token_balance)$ Profile
        +get_profile(user_id)$ Profile
        +update_profile(user_id, kwargs)$ Profile
        +delete_profile(user_id)$ void
        +create_token_record(user, amount, type)$ TokenRecord
        +get_token_record(record_id)$ TokenRecord
        +list_token_records(user_id)$ QuerySet
        +update_token_record(record_id, kwargs)$ TokenRecord
        +delete_token_record(record_id)$ void
        +create_library(user)$ Library
        +get_library(user_id)$ Library
        +delete_library(user_id)$ void
        +create_folder(library, name)$ Folder
        +get_folder(folder_id)$ Folder
        +list_folders(library_id)$ QuerySet
        +update_folder(folder_id, kwargs)$ Folder
        +delete_folder(folder_id)$ void
        +create_song(user, title, kwargs)$ Song
        +get_song(song_id)$ Song
        +list_songs(filters)$ QuerySet
        +update_song(song_id, kwargs)$ Song
        +delete_song(song_id)$ void
    }

    User "1" -- "1" Profile : has
    User "1" -- "0..*" TokenRecord : has
    User "1" -- "1" Library : has
    User "1" -- "0..*" Song : has
    Library "1" -- "0..*" Folder : has
    Folder "1" -- "0..*" Song : keeps

    MusicController ..> User : manages
    MusicController ..> Profile : manages
    MusicController ..> TokenRecord : manages
    MusicController ..> Library : manages
    MusicController ..> Folder : manages
    MusicController ..> Song : manages
```

## Sequence Diagram (CRUD Operations)

```mermaid
sequenceDiagram
    participant Client
    participant Controller as MusicController
    participant DB as Database

    Note over Client, DB: === CREATE ===

    Client->>Controller: create_user("Alice", "alice@example.com", CREATOR)
    Controller->>DB: User.objects.create(...)
    DB-->>Controller: User instance
    Controller-->>Client: User

    Client->>Controller: create_profile(alice, token_balance=100)
    Controller->>DB: Profile.objects.create(...)
    DB-->>Controller: Profile instance
    Controller-->>Client: Profile

    Client->>Controller: create_library(alice)
    Controller->>DB: Library.objects.create(...)
    DB-->>Controller: Library instance
    Controller-->>Client: Library

    Client->>Controller: create_folder(library, "Pop Songs")
    Controller->>DB: Folder.objects.create(...)
    DB-->>Controller: Folder instance
    Controller-->>Client: Folder

    Client->>Controller: create_song(alice, "Sunshine Melody", genre="Pop", ...)
    Controller->>DB: Song.objects.create(...)
    DB-->>Controller: Song instance
    Controller-->>Client: Song

    Note over Client, DB: === READ ===

    Client->>Controller: list_users()
    Controller->>DB: User.objects.filter(...)
    DB-->>Controller: QuerySet
    Controller-->>Client: [User, ...]

    Client->>Controller: get_profile(user_id)
    Controller->>DB: get_object_or_404(Profile, user_id)
    DB-->>Controller: Profile instance
    Controller-->>Client: Profile

    Client->>Controller: list_songs(user=alice)
    Controller->>DB: Song.objects.filter(user=alice)
    DB-->>Controller: QuerySet
    Controller-->>Client: [Song, ...]

    Note over Client, DB: === UPDATE ===

    Client->>Controller: update_song(song_id, status="Completed", is_public=True)
    Controller->>DB: Song.objects.filter(pk).update(...)
    DB-->>Controller: updated
    Controller->>DB: Song.objects.get(pk)
    DB-->>Controller: Song instance
    Controller-->>Client: Song

    Client->>Controller: update_folder(folder_id, name="Favourite Pop")
    Controller->>DB: Folder.objects.filter(pk).update(...)
    DB-->>Controller: updated
    Controller->>DB: Folder.objects.get(pk)
    DB-->>Controller: Folder instance
    Controller-->>Client: Folder

    Note over Client, DB: === DELETE ===

    Client->>Controller: delete_song(song_id)
    Controller->>DB: get_object_or_404(Song, pk)
    DB-->>Controller: Song instance
    Controller->>DB: song.delete()
    DB-->>Controller: deleted
    Controller-->>Client: void
```
