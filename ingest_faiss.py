import fitz  # PyMuPDF
import faiss
import pickle
import numpy as np
from openai import AzureOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# CONFIG
PDF_PATH ="standards-of-care-2026.pdf"
DIM = 1536                 # choose any size you want
CHUNK_SIZE = 800
OVERLAP = 150

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# 1. READ PDF
def read_pdf(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


# 2. SIMPLE CHUNKER
def chunk_text(text, chunk_size, overlap):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap

    return chunks


# 3. EMBEDDING FUNCTION
def embed(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        dimensions=DIM
    )
    return response.data[0].embedding


# 4. MAIN INGESTION
def main():
    print("Reading PDF...")
    text = read_pdf(PDF_PATH)

    print("Chunking...")
    chunks = chunk_text(text, CHUNK_SIZE, OVERLAP)
    print(f"Total chunks: {len(chunks)}")

    print("Creating FAISS index...")
    index = faiss.IndexFlatL2(DIM)

    vectors = []
    stored_texts = []

    for i, chunk in enumerate(chunks):
        vec = embed(chunk)
        vectors.append(vec)
        stored_texts.append(chunk)

        if i % 20 == 0:
            print(f"Embedded {i}/{len(chunks)}")

    vectors = np.array(vectors).astype("float32")

    index.add(vectors)

    print("Saving index...")
    faiss.write_index(index, "diabetes_index.faiss")

    with open("texts.pkl", "wb") as f:
        pickle.dump(stored_texts, f)

    print("✅ FAISS ingestion complete!")


if __name__ == "__main__":
    main()
