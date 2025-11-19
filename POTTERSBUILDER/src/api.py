from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import pickle
from sentence_transformers import SentenceTransformer
import faiss
import uvicorn
import traceback
from typing import Any, Dict
import glob
import requests
import re

try:
    import openai
except Exception:
    openai = None

app = FastAPI(title='POTTERSBUILDER API')

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    use_openai: bool = False
    use_web: bool = False
    web_max_sites: int = 3

# Load index & metadata lazily
INDEX_PATH = os.environ.get('PB_INDEX_PATH', 'vector_index.faiss')
META_PATH = os.environ.get('PB_META_PATH', 'docs.pkl')
_model = None
_index = None
_metas = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def load_index():
    global _index, _metas
    if _index is None or _metas is None:
        # Use local copies so we don't shadow globals when assigning
        index_path = INDEX_PATH
        meta_path = META_PATH

        # Auto-detect index/meta files if defaults are missing
        if not os.path.exists(index_path):
            found = glob.glob('**/*.faiss', recursive=True)
            if found:
                index_path = found[0]
        if not os.path.exists(meta_path):
            foundm = glob.glob('**/*.pkl', recursive=True)
            if foundm:
                meta_path = foundm[0]

        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            raise RuntimeError('Index or metadata not found. Run ingest first or set PB_INDEX_PATH/PB_META_PATH.')

        _index = faiss.read_index(index_path)
        with open(meta_path, 'rb') as f:
            _metas = pickle.load(f)
    return _index, _metas


def include_web_contexts(query, max_sites=3):
    try:
        from src.scrape import search_and_fetch
    except Exception:
        return []
    try:
        web = search_and_fetch(query, max_results=max_sites)
    except Exception:
        return []
    contexts = []
    for w in web:
        contexts.append({'score': 0.0, 'text': w['text'], 'source': w['source']})
    return contexts


def extractive_summary_from_contexts(contexts, max_sentences=4):
    """Build a short extractive summary by taking leading sentences from top-ranked contexts.
    This is a light-weight fallback when no LLM is available.
    """
    if not contexts:
        return None
    sentences = []
    seen = set()
    for ctx in contexts:
        text = ctx.get('text', '')
        # split into candidate sentences
        parts = re.split(r'(?<=[\.\!?])\s+', text.strip())
        for p in parts:
            s = p.strip()
            if not s:
                continue
            # normalize for dedupe
            key = s.lower()
            if key in seen:
                continue
            seen.add(key)
            sentences.append(s)
            if len(sentences) >= max_sentences:
                break
        if len(sentences) >= max_sentences:
            break
    return ' '.join(sentences)


def call_local_llm(prompt: str, max_tokens: int = 400, timeout: int = 30) -> str:
    """Attempt to call a local LLM inference endpoint set by LOCAL_LLM_URL.

    The function tries a few common payload shapes (HuggingFace `inputs`, text-generation-webui `prompt`,
    and OpenAI-like chat/text payloads) and returns the first usable text found.
    """
    url = os.environ.get('LOCAL_LLM_URL')
    if not url:
        return None
    candidate_payloads = [
        {'inputs': prompt},
        {'prompt': prompt, 'max_new_tokens': max_tokens},
        {'prompt': prompt, 'max_tokens': max_tokens},
        {'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': max_tokens},
        {'inputs': {'text': prompt}}
    ]
    headers = {'Content-Type': 'application/json'}
    for payload in candidate_payloads:
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=timeout)
        except Exception:
            continue
        if r.status_code != 200:
            # try next payload shape
            continue
        # try to parse JSON
        try:
            j = r.json()
        except Exception:
            # return raw text body as fallback
            text = r.text
            if text and text.strip():
                return text.strip()
            continue
        # Common response formats
        if isinstance(j, dict):
            # HuggingFace Inference: {'generated_text': '...'} or [{'generated_text': '...'}]
            if 'generated_text' in j and j['generated_text']:
                return j['generated_text'].strip()
            if 'text' in j and j['text']:
                return j['text'].strip()
            if 'choices' in j and isinstance(j['choices'], list) and len(j['choices'])>0:
                c0 = j['choices'][0]
                if isinstance(c0, dict) and 'text' in c0 and c0['text']:
                    return c0['text'].strip()
                if isinstance(c0, dict) and 'message' in c0 and isinstance(c0['message'], dict) and 'content' in c0['message']:
                    return c0['message']['content'].strip()
            # text-generation-inference style: {'results':[{'generated_text':'...'}]}
            if 'results' in j and isinstance(j['results'], list) and len(j['results'])>0:
                r0 = j['results'][0]
                if 'text' in r0 and r0['text']:
                    return r0['text'].strip()
                if 'generated_text' in r0 and r0['generated_text']:
                    return r0['generated_text'].strip()
        elif isinstance(j, list) and len(j) > 0 and isinstance(j[0], dict):
            if 'generated_text' in j[0]:
                return j[0]['generated_text'].strip()
        # If nothing matched, try raw text
        text = r.text
        if text and text.strip():
            return text.strip()
    return None


@app.post('/query')
def query(req: QueryRequest):
    try:
        model = get_model()
        index, metas = load_index()
        q_emb = model.encode([req.query], convert_to_numpy=True)
        faiss.normalize_L2(q_emb)
        D, I = index.search(q_emb.astype('float32'), req.top_k)
        results = []
        for score, idx in zip(D[0], I[0]):
            if idx < 0 or idx >= len(metas):
                continue
            m = metas[idx]
            results.append({'score': float(score), 'text': m['text'], 'source': m.get('source')})
        # Optionally include web contexts
        if req.use_web:
            web_ctxs = include_web_contexts(req.query, max_sites=req.web_max_sites)
            if web_ctxs:
                results.extend(web_ctxs)
        answer = None
        # If requested, attempt LLM synthesis via OpenAI
        if req.use_openai:
            key = os.environ.get('OPENAI_API_KEY')
            if key and openai is not None:
                openai.api_key = key
                # Attempt to use a prompt template if provided
                prompt_template_path = os.environ.get('PB_PROMPT_TEMPLATE') or 'src/prompt_templates/colonial_prompt.txt'
                prompt_parts = []
                if prompt_template_path and os.path.exists(prompt_template_path):
                    try:
                        with open(prompt_template_path, 'r', encoding='utf-8') as pf:
                            prompt_parts.append(pf.read())
                    except Exception:
                        pass
                else:
                    prompt_parts.append('You are an assistant. Use only the context below to answer the question.')

                prompt_parts.append('\n---CONTEXT---\n')
                for i, c in enumerate(results):
                    prompt_parts.append(f"Source {i+1}: {c.get('source','unknown')}\n{c['text']}\n")
                prompt_parts.append('\n---QUESTION---\n')
                prompt_parts.append(req.query)
                user_prompt = '\n'.join(prompt_parts)
                resp = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=[{'role':'system','content':'Answer using only the provided context and cite sources by number.'},{'role':'user','content':user_prompt}], max_tokens=400)
                answer = resp['choices'][0]['message']['content'].strip()
            else:
                # OpenAI not configured — try local LLM if available
                user_prompt = None
                try:
                    prompt_template_path = os.environ.get('PB_PROMPT_TEMPLATE') or 'src/prompt_templates/colonial_prompt.txt'
                    prompt_parts = []
                    if prompt_template_path and os.path.exists(prompt_template_path):
                        try:
                            with open(prompt_template_path, 'r', encoding='utf-8') as pf:
                                prompt_parts.append(pf.read())
                        except Exception:
                            pass
                    else:
                        prompt_parts.append('You are an assistant. Use only the context below to answer the question.')
                    prompt_parts.append('\n---CONTEXT---\n')
                    for i, c in enumerate(results):
                        prompt_parts.append(f"Source {i+1}: {c.get('source','unknown')}\n{c['text']}\n")
                    prompt_parts.append('\n---QUESTION---\n')
                    prompt_parts.append(req.query)
                    user_prompt = '\n'.join(prompt_parts)
                except Exception:
                    user_prompt = req.query

                local_resp = call_local_llm(user_prompt, max_tokens=400)
                if local_resp:
                    answer = local_resp.strip()
                else:
                    # fall back to extractive summary
                    answer = extractive_summary_from_contexts(results, max_sentences=4)
                    if not answer:
                        answer = 'OpenAI integration not configured; returning retrieved contexts.'
        else:
            # No LLM requested: prefer a local LLM if configured, otherwise provide an extractive summary
            local_url = os.environ.get('LOCAL_LLM_URL')
            if local_url:
                # build a simple prompt from contexts
                try:
                    prompt_template_path = os.environ.get('PB_PROMPT_TEMPLATE') or 'src/prompt_templates/colonial_prompt.txt'
                    prompt_parts = []
                    if prompt_template_path and os.path.exists(prompt_template_path):
                        try:
                            with open(prompt_template_path, 'r', encoding='utf-8') as pf:
                                prompt_parts.append(pf.read())
                        except Exception:
                            pass
                    else:
                        prompt_parts.append('You are an assistant. Use only the context below to answer the question.')
                    prompt_parts.append('\n---CONTEXT---\n')
                    for i, c in enumerate(results):
                        prompt_parts.append(f"Source {i+1}: {c.get('source','unknown')}\n{c['text']}\n")
                    prompt_parts.append('\n---QUESTION---\n')
                    prompt_parts.append(req.query)
                    user_prompt = '\n'.join(prompt_parts)
                except Exception:
                    user_prompt = req.query
                local_resp = call_local_llm(user_prompt, max_tokens=400)
                if local_resp:
                    answer = local_resp.strip()
                else:
                    answer = extractive_summary_from_contexts(results, max_sentences=4)
            else:
                answer = extractive_summary_from_contexts(results, max_sentences=4)
            # if no summary could be produced, leave answer as None so frontend shows contexts
        return {'query': req.query, 'answer': answer, 'contexts': results}
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(status_code=500, content={'error': str(e), 'traceback': tb})


@app.get('/debug')
def debug():
    """Diagnostic endpoint: attempts to import components and load index/meta.
    Returns JSON with status and any error traces. Safe for local debugging only.
    """
    info: Dict[str, Any] = {}
    # Python executable
    try:
        info['python_executable'] = os.sys.executable
    except Exception:
        info['python_executable'] = None

    # sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer as _ST
        info['sentence_transformers'] = 'ok'
    except Exception:
        info['sentence_transformers'] = traceback.format_exc()

    # faiss
    try:
        import faiss as _fa
        info['faiss'] = 'ok'
    except Exception:
        info['faiss'] = traceback.format_exc()

    # index & meta
    try:
        idx_exists = os.path.exists(INDEX_PATH)
        meta_exists = os.path.exists(META_PATH)
        info['index_path'] = INDEX_PATH
        info['meta_path'] = META_PATH
        info['index_exists'] = idx_exists
        info['meta_exists'] = meta_exists
        if idx_exists:
            try:
                i = faiss.read_index(INDEX_PATH)
                info['index_ntotal'] = int(i.ntotal)
                info['index_dim'] = int(i.d)
            except Exception:
                info['index_load_error'] = traceback.format_exc()
        if meta_exists:
            try:
                with open(META_PATH, 'rb') as f:
                    metas = pickle.load(f)
                info['meta_count'] = len(metas)
            except Exception:
                info['meta_load_error'] = traceback.format_exc()
    except Exception:
        info['index_check_error'] = traceback.format_exc()

    return info


if __name__ == '__main__':
    uvicorn.run('src.api:app', host='127.0.0.1', port=8000, reload=True)
