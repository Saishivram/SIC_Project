import numpy as np
import faiss
import fitz

DIM = 1536

report_index = None
report_chunks = []

def extract_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def build_report_index(pdf_path, embed):
    global report_index, report_chunks

    text = extract_pdf_text(pdf_path)

    report_chunks = [c for c in text.split("\n\n") if len(c.strip()) > 20]

    embeddings = np.array([embed(c) for c in report_chunks])

    report_index = faiss.IndexFlatL2(DIM)
    report_index.add(embeddings)


def search_report(query, embed, top_k=3):
    q = embed(query).reshape(1, -1)
    _, I = report_index.search(q, top_k)
    return "\n".join([report_chunks[i] for i in I[0]])
