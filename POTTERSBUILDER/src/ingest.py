import os
import glob
import argparse
import pickle
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss


def read_files(data_dir):
    patterns = ["**/*.md", "**/*.txt"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(data_dir, p), recursive=True))
    return files


def chunk_text(text, max_chars=1000, overlap=200):
    if len(text) <= max_chars:
        yield text
        return
    start = 0
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]
        yield chunk
        if end >= len(text):
            break
        start = end - overlap


def build_index(data_dir, index_path, meta_path, model_name="all-MiniLM-L6-v2"):
    model = SentenceTransformer(model_name)
    files = read_files(data_dir)
    texts = []
    metas = []
    for file_idx, filepath in enumerate(sorted(files)):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                raw = f.read()
        except Exception as e:
            print(f"Failed reading {filepath}: {e}")
            continue
        for chunk_idx, chunk in enumerate(chunk_text(raw)):
            doc = {
                'id': f"{file_idx}-{chunk_idx}",
                'text': chunk,
                'source': os.path.relpath(filepath, data_dir)
            }
            metas.append(doc)
            texts.append(chunk)

    if not texts:
        raise ValueError("No texts found in data directory.")

    print(f"Embedding {len(texts)} chunks with model {model_name}...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings.astype('float32'))
    faiss.write_index(index, index_path)
    print(f"Wrote FAISS index to {index_path}")
    with open(meta_path, 'wb') as f:
        pickle.dump(metas, f)
    print(f"Wrote metadata (docs) to {meta_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=str, default='data')
    parser.add_argument('--index-path', type=str, default='vector_index.faiss')
    parser.add_argument('--meta-path', type=str, default='docs.pkl')
    args = parser.parse_args()
    build_index(args.data_dir, args.index_path, args.meta_path)
