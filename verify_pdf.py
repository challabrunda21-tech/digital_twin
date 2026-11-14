import os
import pypdf

pdf_path = os.path.join(os.path.dirname(__file__), "AI_Based_Digital_Twin_Patent_Draft.pdf")
if not os.path.exists(pdf_path):
    pdf_path = "AI_Based_Digital_Twin_Patent_Draft.pdf"

reader = pypdf.PdfReader(pdf_path)
print(f"Total Pages: {len(reader.pages)}")

for i, page in enumerate(reader.pages):
    text = page.extract_text() or ""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    first_line = lines[0] if lines else "EMPTY"
    last_line = lines[-1] if lines else "EMPTY"
    print(f"Page {i+1}: {len(lines)} lines | First: {first_line[:40]} | Last: {last_line[:40]}")
