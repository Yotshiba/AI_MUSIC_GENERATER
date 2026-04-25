from django import forms as django_forms
from django.contrib import admin
from django.contrib import messages as dj_messages
from django.contrib.admin import helpers
from django.template.response import TemplateResponse

from .controllers.admin_token import AdminTokenController
from .models import Folder, GenerationLog, Library, Profile, Song, TokenRecord, User


class GrantTokensForm(django_forms.Form):
    amount = django_forms.IntegerField(
        min_value=1,
        max_value=9999,
        label='Tokens to grant per user',
    )


def grant_tokens_action(modeladmin, request, queryset):
    """Bulk action: grant a fixed number of tokens to all selected users."""
    if 'apply' in request.POST:
        form = GrantTokensForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            count = 0
            for user in queryset:
                try:
                    profile = Profile.objects.get(user=user)
                    new_balance = min(
                        profile.token_balance + amount,
                        Profile.MAX_BALANCE,
                    )
                    AdminTokenController.set_token_balance(user.pk, new_balance)
                    count += 1
                except Exception:
                    pass
            modeladmin.message_user(
                request,
                f'Granted {amount} token(s) to {count} user(s).',
                dj_messages.SUCCESS,
            )
            return None
    else:
        form = GrantTokensForm()

    return TemplateResponse(request, 'admin/grant_tokens.html', {
        'title': 'Grant Tokens',
        'form': form,
        'queryset': queryset,
        'opts': modeladmin.model._meta,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
    })


grant_tokens_action.short_description = 'Grant tokens to selected users'


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
    actions = [grant_tokens_action]


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


@admin.register(GenerationLog)
class GenerationLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'title', 'provider', 'status')
    list_filter = ('status', 'provider')
    search_fields = ('title', 'user__name', 'user__email')
    date_hierarchy = 'timestamp'
    readonly_fields = ('user', 'song', 'title', 'genre', 'mood', 'occasion', 'singer_style', 'topic', 'provider', 'status', 'timestamp')
