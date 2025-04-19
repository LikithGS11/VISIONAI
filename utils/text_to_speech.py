import pyttsx3

# Converts text to speech and saves it to an audio file.
def text_to_speech(text, output_audio_path="audio/output_audio.mp3"):
    engine = pyttsx3.init()
    try:
        # Save speech to the specified file path
        engine.save_to_file(text, output_audio_path)
        engine.runAndWait()
    except Exception as e:
        raise RuntimeError(f"Error generating speech: {e}")
