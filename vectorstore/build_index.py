import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import os

CSV_PATH = os.path.join("..", "data", "complaints-2026-09-07_11_28.csv")
CHROMA_PATH = os.path.join("..", "vectorstore", "chroma_db")

def build_index():
    print("Loading complaints data...")
    df = pd.read_csv(CSV_PATH)

    # Keep only rows with actual complaint text
    df = df.dropna(subset=["Consumer complaint narrative"])
    df = df[df["Consumer complaint narrative"].str.strip() != ""]
    print(f"Found {len(df)} complaints with narrative text")

    # Limit to a manageable number for a portfolio project (optional, speeds things up)
    if len(df) > 2000:
        df = df.sample(2000, random_state=42)
        print(f"Sampled down to {len(df)} complaints for faster indexing")

    print("Loading embedding model (this may take a minute the first time)...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    print("Generating embeddings...")
    narratives = df["Consumer complaint narrative"].tolist()
    embeddings = embedder.encode(narratives, show_progress_bar=True).tolist()

    print("Storing in ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name="complaints")

    ids = [str(cid) for cid in df["Complaint ID"].tolist()]
    metadatas = [
        {
            "product": str(row["Product"]),
            "issue": str(row["Issue"]),
            "company": str(row["Company"])
        }
        for _, row in df.iterrows()
    ]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=narratives,
        metadatas=metadatas
    )

    print(f"Done! Indexed {len(narratives)} complaints into ChromaDB at {CHROMA_PATH}")

if __name__ == "__main__":
    build_index()