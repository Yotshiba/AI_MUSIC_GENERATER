"""
Unified controller providing CRUD operations for all domain models.
"""

from django.shortcuts import get_object_or_404

from .models import Folder, Library, Profile, Song, TokenRecord, User


class MusicController:
    """Single controller handling CRUD for every domain model."""

    # ── User ─────────────────────────────────────────────────────────────

    @staticmethod
    def create_user(name, email, role=User.UserRole.CREATOR):
        return User.objects.create(name=name, email=email, role=role)

    @staticmethod
    def get_user(user_id):
        return get_object_or_404(User, pk=user_id)

    @staticmethod
    def list_users(**filters):
        return User.objects.filter(**filters)

    @staticmethod
    def update_user(user_id, **kwargs):
        User.objects.filter(pk=user_id).update(**kwargs)
        return User.objects.get(pk=user_id)

    @staticmethod
    def delete_user(user_id):
        get_object_or_404(User, pk=user_id).delete()

    # ── Profile ──────────────────────────────────────────────────────────

    @staticmethod
    def create_profile(user, token_balance=0):
        return Profile.objects.create(user=user, token_balance=token_balance)

    @staticmethod
    def get_profile(user_id):
        return get_object_or_404(Profile, user_id=user_id)

    @staticmethod
    def update_profile(user_id, **kwargs):
        Profile.objects.filter(user_id=user_id).update(**kwargs)
        return Profile.objects.get(user_id=user_id)

    @staticmethod
    def delete_profile(user_id):
        get_object_or_404(Profile, user_id=user_id).delete()

    # ── TokenRecord ──────────────────────────────────────────────────────

    @staticmethod
    def create_token_record(user, amount, type):
        return TokenRecord.objects.create(user=user, amount=amount, type=type)

    @staticmethod
    def get_token_record(record_id):
        return get_object_or_404(TokenRecord, pk=record_id)

    @staticmethod
    def list_token_records(user_id):
        return TokenRecord.objects.filter(user_id=user_id)

    @staticmethod
    def update_token_record(record_id, **kwargs):
        TokenRecord.objects.filter(pk=record_id).update(**kwargs)
        return TokenRecord.objects.get(pk=record_id)

    @staticmethod
    def delete_token_record(record_id):
        get_object_or_404(TokenRecord, pk=record_id).delete()

    # ── Library ──────────────────────────────────────────────────────────

    @staticmethod
    def create_library(user):
        return Library.objects.create(user=user)

    @staticmethod
    def get_library(user_id):
        return get_object_or_404(Library, user_id=user_id)

    @staticmethod
    def delete_library(user_id):
        get_object_or_404(Library, user_id=user_id).delete()

    # ── Folder ───────────────────────────────────────────────────────────

    @staticmethod
    def create_folder(library, name):
        return Folder.objects.create(library=library, name=name)

    @staticmethod
    def get_folder(folder_id):
        return get_object_or_404(Folder, pk=folder_id)

    @staticmethod
    def list_folders(library_id):
        return Folder.objects.filter(library_id=library_id)

    @staticmethod
    def update_folder(folder_id, **kwargs):
        Folder.objects.filter(pk=folder_id).update(**kwargs)
        return Folder.objects.get(pk=folder_id)

    @staticmethod
    def delete_folder(folder_id):
        get_object_or_404(Folder, pk=folder_id).delete()

    # ── Song ─────────────────────────────────────────────────────────────

    @staticmethod
    def create_song(user, title, **kwargs):
        return Song.objects.create(user=user, title=title, **kwargs)

    @staticmethod
    def get_song(song_id):
        return get_object_or_404(Song, pk=song_id)

    @staticmethod
    def list_songs(**filters):
        return Song.objects.filter(**filters)

    @staticmethod
    def update_song(song_id, **kwargs):
        Song.objects.filter(pk=song_id).update(**kwargs)
        return Song.objects.get(pk=song_id)

    @staticmethod
    def delete_song(song_id):
        get_object_or_404(Song, pk=song_id).delete()
