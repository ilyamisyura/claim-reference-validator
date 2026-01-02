Implement a **minimal working prototype** inside backend of the workflow based on REQUIREMENTS.md using **LangChain + LangGraph + Deep Agents**.

**Rules**

- Every time you’re unsure about an API/feature, **open the official docs and follow them** (don’t guess).
- Keep it small: stub anything non-essential, but preserve the graph structure and fan-out/fan-in.

**What to build**

1. A LangGraph **top-level workflow** `DocumentWorkflow` with nodes:

   - `extract_claims`
   - `resolve_sources`
   - `ensure_paper_artifacts`
   - `retrieve_evidence`
   - `analyze_claim`
   - `aggregate_report`

2. Use LangGraph **dynamic fan-out**:

   - fan out over claims
   - inside each claim, fan out over sources
   - then reduce back to a per-claim result, then to a final report

3. Use **Deep Agents** for the “analyze_claim” step:

   - create a `ClaimJudge` deep agent that takes `{claim, evidence_chunks}` and returns a strict JSON verdict:
     `{label: supported|contradicted|insufficient, rationale, evidence:[{paper_id, chunk_id, quote}]}`

4. Persistence + caching (prototype-level):

   - file-based cache directory `./artifacts/` for downloaded PDFs / parsed text / chunk indices (store only IDs/paths in state)
   - cache-first fetch for sources; if missing, do a simple HTTP download stub

5. Provide a runnable entrypoint:

   - `python main.py --doc ./sample.txt` prints final report JSON
   - include a tiny `sample.txt`

**Deliverables**

- Clean code, typed models (pydantic), and a short README with how to run.
- Add basic concurrency limits (e.g., semaphore) so fan-out doesn’t explode locally.
