import os
import argparse
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

try:
    import openai
except ImportError:
    openai = None
from src.scrape import search_and_fetch
import os


def load_index(index_path, meta_path):
    # Auto-detect if provided paths are missing
    if not os.path.exists(index_path):
        import glob
        found = glob.glob('**/*.faiss', recursive=True)
        if found:
            index_path = found[0]
    if not os.path.exists(meta_path):
        import glob
        foundm = glob.glob('**/*.pkl', recursive=True)
        if foundm:
            meta_path = foundm[0]

    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Index not found at {index_path}")
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"Metadata not found at {meta_path}")
    index = faiss.read_index(index_path)
    with open(meta_path, 'rb') as f:
        metas = pickle.load(f)
    return index, metas


def semantic_search(query, index, metas, model, top_k=5):
    q_emb = model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(q_emb)
    D, I = index.search(q_emb.astype('float32'), top_k)
    results = []
    for score, idx in zip(D[0], I[0]):
        if idx < 0 or idx >= len(metas):
            continue
        m = metas[idx]
        results.append({'score': float(score), 'text': m['text'], 'source': m.get('source')})
    return results


def synthesize_answer_with_openai(query, contexts, openai_api_key=None):
    if openai is None:
        raise RuntimeError('openai package not installed')
    if openai_api_key:
        openai.api_key = openai_api_key
    # Load prompt template if provided via env PB_PROMPT_TEMPLATE
    prompt_template_path = os.environ.get('PB_PROMPT_TEMPLATE')
    if prompt_template_path and os.path.exists(prompt_template_path):
        try:
            with open(prompt_template_path, 'r', encoding='utf-8') as pf:
                template = pf.read()
        except Exception:
            template = None
    else:
        template = None

    if template:
        prompt_parts = [template]
    else:
        prompt_parts = ["You are an assistant that answers using only the provided context. If the answer is not in the context, say you don't know."]
    prompt_parts.append('\n---CONTEXT---\n')
    for i, c in enumerate(contexts):
        prompt_parts.append(f"Source {i+1}: {c['source']}\n{c['text']}\n")
    prompt_parts.append('\n---QUESTION---\n')
    prompt_parts.append(query)
    system_prompt = "Use the context to answer concisely and cite sources by number."
    user_prompt = "\n".join(prompt_parts)
    resp = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=400
    )
    return resp['choices'][0]['message']['content'].strip()


def include_web_contexts(query, max_sites=3):
    try:
        web = search_and_fetch(query, max_sites=max_sites)
    except Exception:
        return []
    contexts = []
    for w in web:
        contexts.append({'score': 0.0, 'text': w['text'], 'source': w['source']})
    return contexts


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, required=True)
    parser.add_argument('--index-path', type=str, default='vector_index.faiss')
    parser.add_argument('--meta-path', type=str, default='docs.pkl')
    parser.add_argument('--top-k', type=int, default=5)
    parser.add_argument('--use-openai', action='store_true')
    parser.add_argument('--use-web', action='store_true', help='Search the web for additional contexts')
    parser.add_argument('--openai-key', type=str, default=None)
    args = parser.parse_args()

    model = SentenceTransformer('all-MiniLM-L6-v2')
    index, metas = load_index(args.index_path, args.meta_path)
    results = semantic_search(args.query, index, metas, model, top_k=args.top_k)
    if args.use_web:
        web_ctxs = include_web_contexts(args.query, max_sites=3)
        if web_ctxs:
            results.extend(web_ctxs)
    print("Retrieved contexts:")
    for i, r in enumerate(results, 1):
        print(f"[{i}] (score={r['score']:.4f}) source={r['source']}")
        print(r['text'][:400].replace('\n', ' '))
        print('---')

    if args.use_openai:
        key = args.openai_key or os.environ.get('OPENAI_API_KEY')
        if not key:
            print('OPENAI_API_KEY not set; cannot synthesize.')
        else:
            ans = synthesize_answer_with_openai(args.query, results, openai_api_key=key)
            print('\nSYNTHESIZED ANSWER:\n')
            print(ans)
