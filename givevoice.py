from gtts import gTTS
import google.generativeai as genai
import os

# 🔑 Set your Google Gemini API key
genai.configure(api_key="AIzaSyAZTykQyn2C9gT_rbDAbO5iCV4kWI4fqsI")

INPUT_FILE = r"C:\Users\Qadri Laptop\OneDrive\Documents\Blockchain\Assignment1\Recording.m4a"
OUTPUT_FILE = r"C:\Users\Qadri Laptop\OneDrive\Documents\Blockchain\Assignment1\Generaterecording.m4a"

# ✅ Use Flash model (free tier friendly)
model = genai.GenerativeModel("gemini-1.5-flash")

# Step 1: Transcribe Audio with Gemini
with open(INPUT_FILE, "rb") as f:
    audio_data = f.read()

response = model.generate_content([
    {"mime_type": "audio/m4a", "data": audio_data}
])

# Gemini sometimes returns structured parts; get plain text safely
text = response.text if hasattr(response, "text") else str(response)
print("Transcribed:", text)

# Step 2: Convert text to speech with gTTS
tts = gTTS(text=text, lang="en")
tts.save(OUTPUT_FILE)
print(f" Done! Saved at {OUTPUT_FILE}")
