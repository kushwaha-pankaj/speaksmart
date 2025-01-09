from django.urls import path
from . import views

urlpatterns = [
    # Homepage
    path("", views.index, name="index"),

    # Generate audio
    path("generate-audio/", views.generate_audio, name="generate_audio"),

    # Download audio
    path("download-audio/<str:unique_id>/<str:file_name>/", views.download_audio, name="download_audio"),
]
