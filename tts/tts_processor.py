import sys
import os
import re
import uuid
# Add Kokoro repository to Python path
KOKORO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Kokoro-82M")
if KOKORO_PATH not in sys.path:
    sys.path.append(KOKORO_PATH)
from kokoro import generate
from pydub import AudioSegment
import soundfile as sf
from models import build_model
import torch


# Add eSpeak binary directory to PATH
ESPEAK_PATH = r"C:\Program Files (x86)\eSpeak"
if ESPEAK_PATH not in os.environ["PATH"]:
    os.environ["PATH"] += f";{ESPEAK_PATH}"


# Define available voices
VOICE_NAMES = [
    'af', 'af_bella', 'af_sarah', 'am_adam', 'am_michael',
    'bf_emma', 'bf_isabella', 'bm_george', 'bm_lewis',
    'af_nicole', 'af_sky',
]

def load_model_and_voicepack(selected_voice="af"):
    """
    Load the Kokoro TTS model and the selected voicepack dynamically.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    kokoro_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Kokoro-82M")
    model_path = os.path.join(kokoro_base_dir, "kokoro-v0_19.pth")
    voicepack_path = os.path.join(kokoro_base_dir, "voices", f"{selected_voice}.pt")

    if selected_voice not in VOICE_NAMES:
        raise ValueError(f"Invalid voice selection: {selected_voice}")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not os.path.exists(voicepack_path):
        raise FileNotFoundError(f"Voicepack file not found: {voicepack_path}")

    model = build_model(model_path, device)
    voicepack = torch.load(voicepack_path, weights_only=True).to(device)
    print(f"Model and voicepack loaded successfully. Using voice: {selected_voice}.")
    return model, voicepack


# Preprocess text
def preprocess_text(text):
    """
    Cleans the input text by removing unsupported characters and extra whitespace.
    """
    text = re.sub(r'[^\w\s.,!?\'"-]', '', text)  # Remove unsupported characters
    return " ".join(text.split())

# Split text into chunks of specified word count
def split_text_into_word_chunks(text, max_words=75):
    """
    Splits the input text into chunks of up to `max_words`, maintaining word integrity.
    """
    words = text.split()
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]

# Generate audio for a single chunk
def generate_audio_for_chunk(chunk, model, voicepack, lang, output_folder, chunk_index):
    """
    Generates audio for a single text chunk and saves it as a WAV file.
    """
    try:
        print(f"Generating audio for chunk {chunk_index}...")
        audio, _ = generate(model, chunk, voicepack, lang=lang)

        # Save the audio file
        output_file = os.path.join(output_folder, f"chunk_{chunk_index}.wav")
        sf.write(output_file, audio, 24000)  # Save audio at 24kHz
        print(f"Audio saved: {output_file}")
        return output_file
    except Exception as e:
        print(f"Error generating audio for chunk {chunk_index}: {e}")
        return None

# Merge audio chunks into a single file
def merge_audio_chunks(output_folder, final_output):
    """
    Merges all audio chunks in the output folder into a single audio file.
    """
    print("Merging audio chunks...")
    combined_audio = AudioSegment.empty()

    chunk_files = sorted(
        [os.path.join(output_folder, f) for f in os.listdir(output_folder) if f.startswith("chunk_")],
        key=lambda x: int(x.split("_")[-1].split(".")[0])
    )

    if not chunk_files:
        raise FileNotFoundError("No audio chunks found to merge.")

    for chunk_file in chunk_files:
        audio_segment = AudioSegment.from_file(chunk_file)
        combined_audio += audio_segment

    combined_audio.export(final_output, format="wav")
    print(f"Final merged audio saved as {final_output}")
    return final_output

# Process and save text as audio
def process_script_and_save(model, text, voicepack, lang="a", output_base_folder="audio_chunks", max_words=75):
    """
    Process the text and save the final output to a unique folder.
    Returns the path to the final output file and unique folder.
    """
    # Create a unique folder for this request
    unique_folder = os.path.join(output_base_folder, str(uuid.uuid4()))
    os.makedirs(unique_folder, exist_ok=True)

    # Preprocess the text and split it into chunks
    cleaned_text = preprocess_text(text)
    chunks = split_text_into_word_chunks(cleaned_text, max_words)

    # Generate audio for each chunk
    for i, chunk in enumerate(chunks, start=1):
        print(f"Processing chunk {i}/{len(chunks)}...")
        generate_audio_for_chunk(chunk, model, voicepack, lang=lang, output_folder=unique_folder, chunk_index=i)

    # Merge the generated chunks into a single audio file
    final_output = os.path.join(unique_folder, "final_output.wav")
    merge_audio_chunks(unique_folder, final_output)

    return final_output, unique_folder

