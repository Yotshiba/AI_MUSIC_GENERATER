import datetime
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django_q.tasks import async_task

from .controllers import (
    GenerateMusicController,
    InsufficientTokensError,
    ManageLibraryController,
    ProfanityError,
)
from .models import Library, Profile, Song, User

logger = logging.getLogger("music")


def _get_or_create_music_user(auth_user):
    """Bridge Django auth.User to music.User, provisioning on first login.
    Profile and Library are created automatically via post_save signal (signals.py).
    """
    music_user, _ = User.objects.get_or_create(
        email=auth_user.email,
        defaults={'name': auth_user.get_full_name() or auth_user.username or auth_user.email, 'role': User.UserRole.CREATOR},
    )
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
                async_task('music.tasks.generate_music_task', song.pk, provider)
                messages.success(request, f'"{title}" is being generated. You can navigate freely while it processes.')
                return redirect('music:library')
            except ProfanityError as exc:
                error = str(exc)
            except InsufficientTokensError as exc:
                error = str(exc)
                profile.refresh_from_db()

    return render(request, 'music/generate.html', {'profile': profile, 'error': error})


@login_required
def library_view(request):
    music_user = _get_or_create_music_user(request.user)
    profile = Profile.objects.get(user=music_user)

    genre  = request.GET.get('genre', '').strip()
    mood   = request.GET.get('mood', '').strip()
    search = request.GET.get('search', '').strip()

    tracks_qs = ManageLibraryController.list_tracks(
        music_user,
        genre=genre or None,
        mood=mood or None,
        search=search or None,
    )

    paginator  = Paginator(tracks_qs, 20)
    page_obj   = paginator.get_page(request.GET.get('page'))

    return render(request, 'music/library.html', {
        'tracks': page_obj,
        'page_obj': page_obj,
        'profile': profile,
        'genre': genre,
        'mood': mood,
        'search': search,
        'has_filters': bool(genre or mood or search),
    })


@login_required
@require_POST
def delete_track_view(request, song_id):
    music_user = _get_or_create_music_user(request.user)
    song = Song.objects.filter(pk=song_id, user=music_user).first()
    track_title = song.title if song else 'Track'
    try:
        ManageLibraryController.delete_track(song_id, music_user)
        messages.success(request, f'"{track_title}" has been deleted.')
    except Exception as exc:
        logger.warning("Could not delete song %s for user %s: %s", song_id, music_user, exc)
        messages.error(request, f'Could not delete "{track_title}". Please try again.')
    return redirect('music:library')


@login_required
@require_POST
def toggle_privacy_view(request, song_id):
    music_user = _get_or_create_music_user(request.user)
    ManageLibraryController.toggle_privacy(song_id, music_user)
    return redirect('music:library')


@login_required
def download_track_view(request, song_id):
    """Download the audio file for a completed track (REQ-4.3.6).

    Accepts optional ?format=mp3|wav|flac query param to set the downloaded
    filename extension. The file content is served as-is from the provider
    (typically mp3); no server-side transcoding is performed.
    """
    import requests as http_requests
    music_user = _get_or_create_music_user(request.user)
    song = get_object_or_404(Song, pk=song_id, user=music_user, status=Song.SongStatus.COMPLETED)

    if not song.file_url:
        messages.error(request, 'Audio file is not available for this track.')
        return redirect('music:library')

    fmt = request.GET.get('format', 'mp3').lower()
    if fmt not in ('mp3', 'wav', 'flac'):
        fmt = 'mp3'
    content_type_map = {'mp3': 'audio/mpeg', 'wav': 'audio/wav', 'flac': 'audio/flac'}

    try:
        resp = http_requests.get(song.file_url, timeout=60)
        resp.raise_for_status()
        safe_title = song.title.replace('/', '_').replace('\\', '_').replace('"', '')
        response = HttpResponse(resp.content, content_type=content_type_map[fmt])
        response['Content-Disposition'] = f'attachment; filename="{safe_title}.{fmt}"'
        return response
    except Exception as exc:
        logger.warning("Could not download track %s: %s", song_id, exc)
        messages.error(request, 'Could not download the track. The audio file may be unavailable.')
        return redirect('music:library')


def public_listen_view(request, share_token):
    song = ManageLibraryController.get_public_track(share_token)
    return render(request, 'music/public_listen.html', {'song': song})


@login_required
def generation_status_view(request):
    """
    Polled every 3 s by the frontend status bar JS.
    Returns QUEUED + GENERATING songs and recently-finished (within 30 s) songs.
    """
    music_user = _get_or_create_music_user(request.user)
    cutoff = timezone.now() - datetime.timedelta(seconds=30)
    songs = Song.objects.filter(user=music_user).filter(
        Q(status__in=[Song.SongStatus.QUEUED, Song.SongStatus.GENERATING]) |
        Q(
            status__in=[Song.SongStatus.COMPLETED, Song.SongStatus.FAILED],
            updated_at__gte=cutoff,
        )
    ).values('id', 'title', 'status')
    return JsonResponse({'tasks': list(songs)})
