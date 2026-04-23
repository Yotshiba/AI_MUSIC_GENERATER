import requests
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .controllers import (
    GenerateMusicController,
    InsufficientTokensError,
    ManageLibraryController,
)
from .models import Library, Profile, User
from .services import generate as api_generate


def _get_or_create_music_user(auth_user):
    """Bridge Django auth.User to music.User, provisioning on first login."""
    music_user, created = User.objects.get_or_create(
        email=auth_user.email,
        defaults={'name': auth_user.username, 'role': User.UserRole.CREATOR},
    )
    if created:
        Profile.objects.create(user=music_user, token_balance=10)
        Library.objects.create(user=music_user)
    return music_user


def home_view(request):
    if request.user.is_authenticated:
        return redirect('music:library')
    return redirect('login')


@login_required
def generate_view(request):
    music_user = _get_or_create_music_user(request.user)
    profile = Profile.objects.get(user=music_user)
    error = None

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            error = 'Song name is required.'
        else:
            try:
                song = GenerateMusicController.request_generation(
                    user=music_user,
                    title=title,
                    genre=request.POST.get('genre', '').strip(),
                    mood=request.POST.get('mood', '').strip(),
                    occasion=request.POST.get('occasion', '').strip(),
                    singer_style=request.POST.get('singer_style', '').strip(),
                    topic=request.POST.get('topic', '').strip(),
                )
                try:
                    file_url = api_generate(song)
                    GenerateMusicController.mark_complete(song.pk, file_url=file_url)
                    return redirect('music:library')
                except (requests.RequestException, RuntimeError, TimeoutError) as api_err:
                    GenerateMusicController.mark_failed(song.pk)
                    profile.refresh_from_db()
                    error = f'Generation failed: {api_err}'
            except InsufficientTokensError as exc:
                error = str(exc)
                profile.refresh_from_db()

    return render(request, 'music/generate.html', {'profile': profile, 'error': error})


@login_required
def library_view(request):
    music_user = _get_or_create_music_user(request.user)
    profile = Profile.objects.get(user=music_user)
    tracks = ManageLibraryController.list_tracks(music_user)
    return render(request, 'music/library.html', {'tracks': tracks, 'profile': profile})


@login_required
@require_POST
def delete_track_view(request, song_id):
    music_user = _get_or_create_music_user(request.user)
    ManageLibraryController.delete_track(song_id, music_user)
    return redirect('music:library')


@login_required
@require_POST
def toggle_privacy_view(request, song_id):
    music_user = _get_or_create_music_user(request.user)
    ManageLibraryController.toggle_privacy(song_id, music_user)
    return redirect('music:library')


def public_listen_view(request, share_token):
    song = ManageLibraryController.get_public_track(share_token)
    return render(request, 'music/public_listen.html', {'song': song})
