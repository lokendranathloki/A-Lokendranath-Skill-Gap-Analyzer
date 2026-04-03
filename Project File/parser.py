import os
from PyPDF2 import PdfReader
from docx import Document

def extract_text(path):
    ext = os.path.splitext(path)[1].lower()
    text = ""

    if ext == ".pdf":
        reader = PdfReader(path)
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text()

    elif ext == ".docx":
        doc = Document(path)
        for para in doc.paragraphs:
            text += para.text + "\n"

    elif ext == ".txt":
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

    return text
