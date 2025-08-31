from pathlib import Path
from gtts import gTTS
import PyPDF2
import re
import tempfile
import shutil

# Extract text from a PDF file
def pdf_to_text(file_path: str) -> str:
    text_data = []
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text_data.append(content)
    return "\n".join(text_data)

# Break text into smaller pieces
def chunk_text(content: str, limit: int = 150) -> list[str]:
    clean_text = re.sub(r"\s+", " ", content).strip()
    words = clean_text.split()
    
    result, buf = [], []
    length = 0
    
    for word in words:
        if length + len(word) + 1 <= limit:
            buf.append(word)
            length += len(word) + 1
        else:
            result.append(" ".join(buf))
            buf = [word]
            length = len(word)
    if buf:
        result.append(" ".join(buf))
    return result

# Convert text chunks into mp3 files
def text_to_audio(chunks: list[str], output_dir: str = "audio_output"):
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    for idx, part in enumerate(chunks, 1):
        try:
            tts = gTTS(text=part, lang="en")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tts.save(tmp.name)
                tmp_file = Path(tmp.name)

            if tmp_file.stat().st_size > 1024:  # at least 1 KB
                final_name = output_path / f"segment_{idx}.mp3"
                shutil.move(str(tmp_file), final_name)
                print(f"[✔] Saved {final_name}")
            else:
                print(f"[!] Skipped empty segment {idx}")
                tmp_file.unlink()

        except Exception as e:
            print(f"[x] Failed at segment {idx}: {e}")

# ----------- RUNNING PART -------------
if __name__ == "__main__":
    pdf_file = r"C:\Users\Qadri Laptop\OneDrive\Documents\GenerativeAI\Life3.0.pdf"
    
    text_data = pdf_to_text(pdf_file)
    segments = chunk_text(text_data, limit=150)
    text_to_audio(segments, output_dir="audiobook_segments")

    print("\n Conversion completed. Check 'audiobook_segments' folder.")
