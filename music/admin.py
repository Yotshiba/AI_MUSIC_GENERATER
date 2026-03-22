from django.contrib import admin

from .models import Folder, Library, Profile, Song, TokenRecord, User


class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 0


class LibraryInline(admin.StackedInline):
    model = Library
    extra = 0


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'role')
    search_fields = ('name', 'email')
    list_filter = ('role',)
    inlines = [ProfileInline, LibraryInline]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'token_balance')


@admin.register(TokenRecord)
class TokenRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'type')
    list_filter = ('type',)


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ('user',)


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'library')


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'genre', 'mood', 'status', 'is_public')
    list_filter = ('status', 'is_public', 'genre')
    search_fields = ('title', 'topic')
