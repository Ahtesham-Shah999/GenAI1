from pathlib import Path

folder = Path(r"C:\Users\Qadri Laptop\OneDrive\Documents\GenerativeAI\Assignement1\audiobook_segments")
output_file = folder / "merged_simple.mp3"

with open(output_file, "wb") as outfile:
    for mp3 in sorted(folder.glob("*.mp3")):
        with open(mp3, "rb") as infile:
            outfile.write(infile.read())

print(f" Merged into {output_file}")
