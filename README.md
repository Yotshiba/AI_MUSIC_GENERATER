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

## Project Structure

```
ai_music_generator/     # Django project settings
music/
  models.py             # Domain models (User, Profile, TokenRecord, Library, Folder, Song)
  admin.py              # Django Admin registration for CRUD
  management/commands/
    seed_and_demo.py    # Management command demonstrating CRUD operations
  migrations/           # Database migration files
```
