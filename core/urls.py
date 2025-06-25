# core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('worship-info-input/', views.worship_info_input_view, name='worship_info_input'),
    path('song-info-input/', views.song_info_input_view, name='song_info_input'),
    path('ppt-creation-start/', views.ppt_creation_start_view, name='ppt_creation_start'),
    path('ppt-download/<int:ppt_request_id>/', views.ppt_download_view, name='ppt_download'),
    path('api/ppt-status/<str:task_id>/', views.ppt_task_status_api, name='ppt_task_status_api'),
]
