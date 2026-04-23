import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .controllers import (
    GenerateMusicController,
    InsufficientTokensError,
    ManageLibraryController,
)
from .models import Library, Profile, Song, User
from .profanity import contains_profanity


def _get_or_create_music_user(auth_user):
    """Bridge Django auth.User to music.User, provisioning on first login."""
    music_user, created = User.objects.get_or_create(
        email=auth_user.email,
        defaults={'name': auth_user.get_full_name() or auth_user.username or auth_user.email, 'role': User.UserRole.CREATOR},
    )
    if created:
        Profile.objects.create(user=music_user, token_balance=10)
        Library.objects.create(user=music_user)
    return music_user


def home_view(request):
    if request.user.is_authenticated:
        return redirect('music:library')
    return redirect('account_login')


@login_required
def generate_view(request):
    music_user = _get_or_create_music_user(request.user)
    profile = Profile.objects.get(user=music_user)
    error = None

    if request.method == 'POST':
        title        = request.POST.get('title', '').strip()
        genre        = request.POST.get('genre', '').strip()
        mood         = request.POST.get('mood', '').strip()
        occasion     = request.POST.get('occasion', '').strip()
        singer_style = request.POST.get('singer_style', '').strip()
        topic        = request.POST.get('topic', '').strip()
        provider     = request.POST.get('provider', 'mureka').strip()

        if not title:
            error = 'Song name is required.'
        elif any(contains_profanity(f) for f in [title, mood, topic, genre]):
            error = 'Your input contains inappropriate language. Please revise to comply with platform safety guidelines.'
        else:
            try:
                song = GenerateMusicController.request_generation(
                    user=music_user,
                    title=title,
                    genre=genre,
                    mood=mood,
                    occasion=occasion,
                    singer_style=singer_style,
                    topic=topic,
                    provider=provider,
                )
                from django_q.tasks import async_task
                async_task('music.tasks.generate_music_task', song.pk, provider)
                messages.success(request, f'"{title}" is being generated. You can navigate freely while it processes.')
                return redirect('music:library')
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
    song = Song.objects.filter(pk=song_id, user=music_user).first()
    track_title = song.title if song else 'Track'
    ManageLibraryController.delete_track(song_id, music_user)
    messages.success(request, f'"{track_title}" has been deleted.')
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


@login_required
def generation_status_view(request):
    """
    Polled every 3 s by the frontend status bar JS.
    Returns GENERATING songs and recently-finished (within 30 s) songs.
    """
    music_user = _get_or_create_music_user(request.user)
    cutoff = timezone.now() - datetime.timedelta(seconds=30)
    songs = Song.objects.filter(user=music_user).filter(
        Q(status=Song.SongStatus.GENERATING) |
        Q(
            status__in=[Song.SongStatus.COMPLETED, Song.SongStatus.FAILED],
            updated_at__gte=cutoff,
        )
    ).values('id', 'title', 'status')
    return JsonResponse({'tasks': list(songs)})
