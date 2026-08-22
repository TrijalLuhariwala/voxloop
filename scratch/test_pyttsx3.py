import pyttsx3

try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    print(f"Total pyttsx3 voices found: {len(voices)}")
    for idx, voice in enumerate(voices):
        print(f"Voice {idx}: ID={voice.id}, Name={voice.name}")
    
    # Save a test wav
    engine.setProperty('rate', 190)
    if len(voices) > 0:
        engine.setProperty('voice', voices[0].id)
    engine.save_to_file("Hello, this is a test male voice response.", "scratch/test_pyttsx3.wav")
    engine.runAndWait()
    print("SUCCESS: scratch/test_pyttsx3.wav generated!")
except Exception as e:
        print(f"pyttsx3 error: {e}")
