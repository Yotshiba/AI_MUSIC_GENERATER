from django.urls import path

from . import views

app_name = 'music'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('generate/', views.generate_view, name='generate'),
    path('library/', views.library_view, name='library'),
    path('library/<int:song_id>/delete/', views.delete_track_view, name='delete_track'),
    path('library/<int:song_id>/toggle-privacy/', views.toggle_privacy_view, name='toggle_privacy'),
    path('listen/<uuid:share_token>/', views.public_listen_view, name='public_listen'),
]
