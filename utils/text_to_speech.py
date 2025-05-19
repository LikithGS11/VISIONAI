import pyttsx3

def text_to_speech(text, output_audio_path="audio/output_audio.wav"):
    engine = pyttsx3.init()
    try:
        engine.save_to_file(text, output_audio_path)
        engine.runAndWait()
    except Exception as e:
        raise RuntimeError(f"Error generating speech: {e}")
