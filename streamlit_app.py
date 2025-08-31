import streamlit as st
import pdfplumber
import pyttsx3
import requests
import tempfile
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
RESEMBLE_API_KEY = os.getenv('RESEMBLE_API_KEY')
RESEMBLE_PROJECT_ID = os.getenv('RESEMBLE_PROJECT_ID')
RESEMBLE_VOICE_ID = os.getenv('RESEMBLE_VOICE_ID')


# 🔧 Check if Resemble AI is configured
def check_resemble_config():
    missing_configs = []
    if not RESEMBLE_API_KEY or RESEMBLE_API_KEY == "#Your Resemble.ai API":
        missing_configs.append("RESEMBLE_API_KEY")
    if not RESEMBLE_PROJECT_ID or RESEMBLE_PROJECT_ID == "#Your Project ID":
        missing_configs.append("RESEMBLE_PROJECT_ID")
    if not RESEMBLE_VOICE_ID or RESEMBLE_VOICE_ID == "#Your Voice ID":
        missing_configs.append("RESEMBLE_VOICE_ID")
    return missing_configs


RESEMBLE_CONFIG_MISSING = check_resemble_config()


# 🎧 Core Class
class AudiobookGenerator:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.local_audio_file = None
        self.cloned_audio_file = None

    def extract_text_from_pdf(self, pdf_file):
        try:
            text = ""
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            st.error(f"⚠ Error extracting text: {str(e)}")
            return None

    def prepare_text(self, text):
        text = text.replace('\n', ' ').replace('\r', ' ')
        return ' '.join(text.split())

    def generate_local_tts(self, text, progress_bar=None):
        try:
            if progress_bar:
                progress_bar.progress(0.1, text="🎙️ Initializing voice engine...")

            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            if voices:
                engine.setProperty('voice', voices[0].id)
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 0.9)

            output_file = os.path.join(self.temp_dir, "local_tts.wav")
            engine.save_to_file(text, output_file)

            if progress_bar:
                progress_bar.progress(0.5, text="🎶 Synthesizing narration...")

            engine.runAndWait()

            if progress_bar:
                progress_bar.progress(1.0, text="✅ Narration generated!")

            self.local_audio_file = output_file
            return True
        except Exception as e:
            st.error(f"⚠ Local TTS error: {str(e)}")
            return False

    def upload_to_temporary_host(self, audio_file):
        try:
            with open(audio_file, 'rb') as f:
                upload_response = requests.post('https://bashupload.com', files={'file': f})
                upload_response.raise_for_status()
                for line in upload_response.text.splitlines():
                    if line.strip().startswith('wget'):
                        return line.strip().split()[1]
            return None
        except Exception as e:
            st.error(f"⚠ Upload error: {str(e)}")
            return None

    def clone_voice_with_resemble(self, audio_file, progress_bar=None):
        try:
            if RESEMBLE_CONFIG_MISSING:
                st.error("❌ Resemble AI not configured properly. Update `.env` file.")
                return None

            if progress_bar:
                progress_bar.progress(0.2, text="☁ Uploading audio...")

            public_url = self.upload_to_temporary_host(audio_file)
            if not public_url:
                return None

            if progress_bar:
                progress_bar.progress(0.4, text="🤖 Sending to Resemble AI...")

            api_url = f"https://app.resemble.ai/api/v2/projects/{RESEMBLE_PROJECT_ID}/clips"
            headers = {'Authorization': f'Token {RESEMBLE_API_KEY}', 'Content-Type': 'application/json'}
            payload = {"voice_uuid": RESEMBLE_VOICE_ID, "body": f"<resemble:convert src='{public_url}'></resemble:convert>"}

            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if data.get('success'):
                clip_uuid = data['item']['uuid']
                clip_url = f"https://app.resemble.ai/api/v2/projects/{RESEMBLE_PROJECT_ID}/clips/{clip_uuid}"

                for i in range(30):
                    response = requests.get(clip_url, headers={'Authorization': f'Token {RESEMBLE_API_KEY}'})
                    response.raise_for_status()
                    data = response.json()
                    if data.get('item') and data['item'].get('audio_src'):
                        audio_src_url = data['item']['audio_src']
                        audio_response = requests.get(audio_src_url)
                        audio_response.raise_for_status()
                        return audio_response.content
                    time.sleep(2)

                st.error("⏳ Voice cloning timed out.")
                return None
            else:
                st.error(f"API error: {data.get('message')}")
                return None
        except Exception as e:
            st.error(f"⚠ Voice cloning error: {str(e)}")
            return None

    def clone_audio(self, progress_bar=None):
        if not self.local_audio_file or not os.path.exists(self.local_audio_file):
            st.error("⚠ Please generate local TTS first.")
            return False
        cloned_audio_data = self.clone_voice_with_resemble(self.local_audio_file, progress_bar)
        if cloned_audio_data:
            self.cloned_audio_file = os.path.join(self.temp_dir, "cloned_audio.wav")
            with open(self.cloned_audio_file, 'wb') as f:
                f.write(cloned_audio_data)
            return True
        return False


# 🚀 Main UI
def main():
    st.set_page_config(page_title="AI Audiobook Studio", page_icon="🎧", layout="wide")

    # Inject CSS
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg,#1E1E2E 30%,#2A2A40 100%); }
        h1,h2,h3 { color:#FF6F61 !important; font-family:'Trebuchet MS',sans-serif; }
        section[data-testid="stSidebar"] { background-color:#2A2A40; color:white; }
        .stButton>button { background:#FF6F61; color:white; border-radius:12px; font-weight:bold; }
        .stButton>button:hover { background:#FF857A; color:black; }
        .stProgress>div>div>div>div { background-color:#FFD166; }
        .streamlit-expanderHeader { background:#2A2A40; color:#FFD166; font-weight:bold; }
        </style>
    """, unsafe_allow_html=True)

    st.title("📘 AI-Powered Audiobook Studio")
    st.markdown("Convert **PDF books** into immersive audiobooks 🎙️ with **local TTS** or **AI voice cloning**.")

    # Session state
    if 'generator' not in st.session_state:
        st.session_state.generator = AudiobookGenerator()
    if 'text_extracted' not in st.session_state:
        st.session_state.text_extracted = False
    if 'local_tts_generated' not in st.session_state:
        st.session_state.local_tts_generated = False
    if 'voice_cloned' not in st.session_state:
        st.session_state.voice_cloned = False
    if 'full_text' not in st.session_state:
        st.session_state.full_text = ""

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Status")
        st.markdown(f"""
        - 📖 Text: {"✅ Extracted" if st.session_state.text_extracted else "⏳ Pending"}  
        - 🎶 Local Narration: {"✅ Ready" if st.session_state.local_tts_generated else "⏳ Pending"}  
        - 🧑‍🎤 Voice Clone: {"✅ Ready" if st.session_state.voice_cloned else "⏳ Pending"}  
        """)
        if RESEMBLE_CONFIG_MISSING:
            st.error("❌ Resemble AI not configured")
        else:
            st.success("✅ Resemble AI Configured")

    # Step 1: Upload
    with st.expander("📤 Step 1: Upload PDF", expanded=True):
        uploaded_file = st.file_uploader("Upload your book (PDF)", type="pdf")
        if uploaded_file:
            with st.spinner("Extracting text..."):
                text = st.session_state.generator.extract_text_from_pdf(uploaded_file)
                if text:
                    st.session_state.full_text = st.session_state.generator.prepare_text(text)
                    st.session_state.text_extracted = True
                    st.success(f"✅ Extracted {len(text)} characters")
                    st.text_area("📖 Preview", value=text[:500] + "..." if len(text) > 500 else text, height=150)

    # Step 2: Local TTS
    with st.expander("🎶 Step 2: Generate Local Narration"):
        if st.session_state.text_extracted and not st.session_state.local_tts_generated:
            if st.button("🚀 Generate Narration"):
                progress = st.progress(0, text="Starting narration...")
                success = st.session_state.generator.generate_local_tts(st.session_state.full_text, progress)
                if success:
                    st.session_state.local_tts_generated = True
                    st.success("✅ Narration ready!")
                    st.experimental_rerun()

        if st.session_state.local_tts_generated and st.session_state.generator.local_audio_file:
            st.audio(st.session_state.generator.local_audio_file, format="audio/wav")
            with open(st.session_state.generator.local_audio_file, "rb") as f:
                st.download_button("⬇️ Download Narration", f.read(), "local_tts.wav", "audio/wav")

    # Step 3: Voice Clone
    with st.expander("🧑‍🎤 Step 3: AI Voice Cloning"):
        if st.session_state.local_tts_generated and not st.session_state.voice_cloned:
            if not RESEMBLE_CONFIG_MISSING:
                if st.button("🤖 Clone with Resemble AI"):
                    progress = st.progress(0, text="Starting cloning...")
                    success = st.session_state.generator.clone_audio(progress)
                    if success:
                        st.session_state.voice_cloned = True
                        st.success("✅ Voice cloned!")
                        st.experimental_rerun()
            else:
                st.warning("⚠️ Resemble AI disabled (missing config)")

        if st.session_state.voice_cloned and st.session_state.generator.cloned_audio_file:
            st.audio(st.session_state.generator.cloned_audio_file, format="audio/wav")
            with open(st.session_state.generator.cloned_audio_file, "rb") as f:
                st.download_button("⬇️ Download Cloned Audiobook", f.read(), "cloned_audiobook.wav", "audio/wav")

    # Reset
    st.markdown("---")
    if st.button("🔁 Restart Workflow"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.experimental_rerun()


if __name__ == "__main__":
    main()
