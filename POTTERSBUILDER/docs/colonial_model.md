# POTTERSBUILDER — Colonialism-focused model guide

This document explains how to create a focused retrieval and (optional) synthesis workflow that targets the colonial period of Kenyan history.

1) Corpus
- Place documents about the colonial period in `data/colonialism/`. Small files are preferred (one chapter/article per file). The sample files included are short summaries suitable for demo and testing.

2) Build a focused index
- Use the existing `src/ingest.py` to build a FAISS index restricted to this folder:

```powershell
python src\ingest.py --data-dir data/colonialism --index-path colonial_index.faiss --meta-path colonial_docs.pkl
```

3) Querying
- Use `src/query.py` and point `--index-path` / `--meta-path` at the colonial index. The `src/prompt_templates/colonial_prompt.txt` file provides a safe prompt template for synthesis.

4) Synthesis (optional)
- If you have an `OPENAI_API_KEY` set on the server, you can use the `--use-openai` flag in `src/query.py` to synthesize answers using the retrieved contexts and the `colonial_prompt.txt` template. Ensure you pass the prompt template contents as the system/user message to the model.

5) Fine-tuning / Supervised Data (next step)
- For a more accurate, specialized LLM you can create supervised fine-tuning data: pairs of (question, grounded_answer) where grounded_answer cites sources. Keep the dataset modest at first (a few hundred examples) and evaluate for hallucinations and factuality.

6) Ethical and provenance notes
- Explicitly track the source of each context (author, title, license). Avoid ingesting copyrighted material without permission. Prefer public-domain, government archives, and properly licensed scholarly works.

7) Testing
- Create a small test set of canonical questions about the colonial period and expected excerpts/answers. Use these to validate that retrieval returns relevant contexts and that synthesis (if used) does not hallucinate.
