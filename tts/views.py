from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import os
import uuid
from datetime import datetime
from .tts_processor import process_script_and_save, load_model_and_voicepack
from django.conf import settings
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Define available voices
VOICE_NAMES = [
    'af', 'af_bella', 'af_sarah', 'am_adam', 'am_michael',
    'bf_emma', 'bf_isabella', 'bm_george', 'bm_lewis',
    'af_nicole', 'af_sky',
]

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_FOLDER = os.path.join(BASE_DIR, "media/audio_chunks")


# Render the homepage
def index(request):
    return render(request, "tts/index.html")


# Generate audio
@csrf_exempt  # Replace with CSRF validation in production
def generate_audio(request):
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        selected_voice = request.POST.get("voice", "af")  # Default to 'af'

        if not text:
            return JsonResponse({"error": "No text provided."}, status=400)

        if selected_voice not in VOICE_NAMES:
            return JsonResponse({"error": f"Invalid voice selected: {selected_voice}"}, status=400)

        # Extract language from the voice name (e.g., 'af' or 'bm')
        lang = 'a'

        # Create a unique folder for this request
        unique_id = str(uuid.uuid4())
        output_folder = os.path.join(MEDIA_FOLDER, unique_id)

        try:
            # Load model and voicepack dynamically
            model, voicepack = load_model_and_voicepack(selected_voice)

            # Generate audio and save it in the unique folder
            final_output, unique_folder = process_script_and_save(
                model, text, voicepack, lang=lang, output_base_folder=MEDIA_FOLDER
            )

            # Construct audio URL
            relative_path = os.path.relpath(final_output, BASE_DIR)
            audio_url = f"/{relative_path.replace(os.sep, '/')}"

            if os.path.exists(final_output):
                # Calculate file size
                file_size = os.path.getsize(final_output)
                file_size_readable = (
                    f"{file_size / 1024 / 1024:.2f} MB" if file_size > 1024 * 1024 else f"{file_size / 1024:.2f} KB"
                )

                return JsonResponse({
                    "message": "Audio generated successfully.",
                    "audio_url": audio_url,
                    "file_size": file_size_readable
                })
            else:
                logger.error(f"File not found after generation: {final_output}")
                return JsonResponse({"error": "Audio generation failed. File not found."}, status=500)

        except Exception as e:
            logger.exception("Error during audio generation")
            return JsonResponse({"error": f"Failed to generate audio: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)

# Download audio
def download_audio(request, unique_id, file_name):
    file_path = os.path.join(settings.MEDIA_ROOT, 'audio_chunks', unique_id, file_name)

    if not os.path.exists(file_path):
        logger.error(f"File not found for download: {file_path}")
        raise Http404("File not found.")

    try:
        logger.info(f"Starting download: {file_name}")
        response = FileResponse(open(file_path, 'rb'), content_type='audio/wav')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        response['Content-Length'] = os.path.getsize(file_path)
        return response
    except IOError as e:
        logger.exception(f"Error serving file: {file_name}")
        return JsonResponse({"error": "Error while downloading file."}, status=500)
