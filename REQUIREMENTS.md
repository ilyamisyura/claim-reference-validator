# Claim–Reference Validation (CGCRV) — Requirements (MVP → V2)

## 0) One-sentence goal

Given an academic document (Bachelor/Master thesis), automatically produce a **human-reviewable map** of **claims / citation spans → cited references → best supporting passages (with page/section anchors) → support verdict + confidence**, highlighting likely mismatches where the citation **does not** support the claim.

> **Non-goal:** “AI detector” or plagiarism policing. The system is an **evidence triage + supervision aid** with calibrated uncertainty.

---

## 1) Primary users & use-cases

### Users

- **Supervisor / examiner**: needs fast triage of citation quality and claim grounding.
- **Student** (optional mode): learns which claims are insufficiently supported and how to fix them.

### Core use-cases

1. Upload thesis → get ranked list of “high-risk” claims/citation spans likely unsupported.
2. Click item → view: claim span, cited paper(s), retrieved evidence passages, page numbers, confidence.
3. Export report to share or archive (JSON + HTML/PDF).
4. Handle common failure cases explicitly (paywall, missing DOI, ambiguous citation scope).

---

## 2) Inputs, outputs, interfaces

### Inputs

- Document file:
  - **MVP**: `.docx` and `.pdf`
  - **V2**: LaTeX source / `.tex` + `.bib`
- Optional: bibliography file (`.bib`) if available
- Optional: local folder of PDFs of cited sources (for paywalled papers)

### Outputs

- **Machine-readable**:
  - `report.json` (full structured output)
  - `items.csv` (flat table for sorting/filtering)
- **Human-readable**:
  - `report.html` (interactive local report)
  - **V2**: `report.pdf` (static)

### Execution

- CLI entrypoint:
  - `cgcrv analyze --input thesis.docx --out out_dir/ [--sources sources_dir/] [--mode supervisor|student]`
- Optional local web UI:
  - `cgcrv serve --report out_dir/report.json`

---

## 3) Functional requirements (MVP)

### FR1 — Document ingestion & structure

- Parse the document into:
  - paragraphs, headings, lists, tables (best-effort), page anchors (for PDFs if feasible)
- Preserve original text offsets for highlighting.
- Identify in-text citations and associate them to **citation spans** (the text likely supported by a citation).

**Citation span definition (MVP heuristic):**

- A sentence containing a citation marker; if multiple sentences in a paragraph have no citations but end with a citation, expand span to previous sentence(s) until a boundary rule triggers.

### FR2 — Citation extraction (styles)

Support at least:

- Numeric: `[1]`, `[1,2]`, `[1–3]`, superscripts if extractable
- Author-year: `(Smith, 2020)`, `(Smith & Doe, 2020; Chan, 2021)`
- LaTeX-ish (in DOCX/PDF text): `\cite{key}` (best-effort)

Output for each span:

- `span_text`, `span_location` (doc offsets), `citations[]` (raw markers)

### FR3 — Reference list parsing & normalization

- Extract bibliography entries from the document if present.
- Normalize references into structured metadata:
  - authors, title, year, venue, DOI (if present), URL (if present)
- Link in-text citations → bibliography entries (best-effort). When unresolved, mark as `unresolved_citation`.

### FR4 — Reference resolution (metadata enrichment)

For each reference (or unresolved citation if possible):

- Resolve DOI / canonical metadata via external APIs **when allowed** (configurable):
  - Crossref / OpenAlex / Semantic Scholar
- Cache results locally to avoid repeated calls.

**Config:** `--offline` disables all network calls and only uses provided PDFs/bibliography.

### FR5 — Full-text acquisition (evidence corpus)

Build an “evidence corpus” per reference:

- Priority order:
  1. User-provided PDF in `--sources` (match by DOI/title fuzzy)
  2. Open-access PDF (via OA resolvers) **if not offline**
  3. Abstract-only fallback (metadata providers) if full text unavailable

If full text unavailable:

- Mark `evidence_level = "abstract_only"` or `"none"`.

### FR6 — PDF/text processing and indexing

- Convert each source PDF to text with page segmentation.
- Chunk text into passages with stable IDs:
  - `paper_id`, `page`, `chunk_id`, `chunk_text`
- Build a per-paper retrieval index:
  - **MVP**: BM25 (sparse) OR hybrid (BM25 + embeddings if available)
- Store chunk→page mapping for display.

### FR7 — Evidence retrieval for each citation span

For each `span` and each cited `paper`:

- Query = span text (or extracted claim sentence)
- Retrieve top-k passages (k configurable, default 5)
- Output:
  - retrieved chunks with `page`, `score_retrieval`, `chunk_text`

### FR8 — Entailment / support scoring (human-in-loop)

For each (span, paper) pair with retrieved passages:

- Compute a support label and confidence:
  - `SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`, `NOT_FOUND`
- Provide minimal rationale:
  - cite which chunk(s) were used as best evidence and why
- **MVP implementation options (choose one, behind an interface):**
  - (A) Local NLI model tuned for scientific text
  - (B) LLM-based scoring (local or API) with strict prompt + quoted evidence
  - (C) Heuristic baseline (lexical overlap + numeric consistency) as fallback

**Important:** the system must expose uncertainty. If evidence is weak or ambiguous, prefer `INSUFFICIENT_EVIDENCE`.

### FR9 — Aggregation into statement–reference relationship graph

Produce a final item list:

- One row per citation span; include:
  - span text, section heading (if known)
  - cited refs
  - best ref verdict (max support), worst ref verdict (min support)
  - overall “risk score” = f(unsupported/confidence, numeric claims, causal language, missing ref)
  - links to evidence snippets with page numbers

### FR10 — Report generation

Generate:

- `report.html`:
  - sortable/filterable table
  - detail panel with highlights and evidence passages (with page numbers)
  - filters: unsupported, low confidence, missing DOI/fulltext, numeric claims, causal claims
- `report.json` with full details.

---

## 4) Non-functional requirements

### NFR1 — Privacy & deployment

- Default: **local-only** processing (no uploads to third parties).
- Network calls must be **opt-in** or disable-able via `--offline`.
- Store only what is necessary. Support `--no-store` mode for ephemeral runs.

### NFR2 — Reproducibility

- Deterministic runs when model seeds are fixed.
- Record all versions:
  - parser version, retrieval model, NLI model, config hash

### NFR3 — Performance targets (MVP)

- Thesis 50–150 pages:
  - Parsing + analysis ≤ 30 minutes on a typical workstation (configurable)
- Incremental caching:
  - Re-analysis should reuse paper indexes and metadata.

### NFR4 — Transparency

- Every verdict must show:
  - which evidence chunks were used
  - confidence score
  - if source unavailable, say so explicitly

### NFR5 — Robustness

- Never crash on malformed PDFs/citations; degrade gracefully:
  - mark as `parse_error` / `unresolved` and continue.

---

## 5) Data model (JSON schema sketch)

### Entities

#### Document

- `doc_id`, `title`, `input_path`, `created_at`, `config`

#### Span (citation span / claim span)

- `span_id`
- `text`
- `doc_offsets`: `{start, end}` (if available)
- `section_path`: `["1 Introduction", "1.2 Background"]` (best-effort)
- `citations_raw`: `string[]`
- `linked_reference_ids`: `string[]`
- `features`: `{has_numbers, has_causal_markers, hedging_level, sentence_count, ...}`

#### Reference

- `reference_id`
- `raw_bib_entry`
- `normalized`: `{title, authors[], year, venue, doi, url}`
- `resolution`: `{provider, resolved_doi, confidence, fetched_at}`
- `evidence_level`: `"fulltext" | "abstract_only" | "none"`
- `source_files`: `{pdf_path?, text_cache_path?}`

#### EvidenceChunk

- `paper_id`, `page`, `chunk_id`, `text`

#### Match / Assessment

- `span_id`, `reference_id`
- `retrieval`: `{method, top_k, chunks:[{chunk_id, page, retrieval_score}]}`
- `assessment`: `{label, confidence, rationale, best_chunk_ids[]}`

### Outputs

- `items[]`: aggregated per-span table rows
- `errors[]`: parse/resolution failures

---

## 6) Heuristics & NLP features (MVP)

To prioritize “risk”:

- Numeric claims: regex for percentages, p-values, CI, n=, years, counts
- Causal language: “causes”, “leads to”, “results in”, “therefore”
- Strong certainty: “proves”, “demonstrates”, “shows that”
- Hedging: “may”, “might”, “suggests”, “could” (lower priority)
- Citation anomalies:
  - citation marker present but no matching bibliography entry
  - bibliography entry exists but DOI/title missing
  - reference is retracted/withdrawn (V2 via external checks)

---

## 7) MVP technical architecture (suggested)

### Pipeline modules

1. `ingest/` — load DOCX/PDF, extract text blocks + offsets
2. `citations/` — detect citation markers, build citation spans, parse bibliography
3. `references/` — normalize + resolve metadata, caching
4. `sources/` — acquire PDFs or abstracts, PDF→text with pages
5. `index/` — chunking + BM25/hybrid indexing per paper
6. `retrieve/` — top-k evidence retrieval for (span, paper)
7. `score/` — entailment/support scoring
8. `report/` — HTML + JSON + CSV generation
9. `cli.py` — orchestration

### Storage

- `out_dir/`
  - `report.json`, `items.csv`, `report.html`
  - `cache/metadata/`, `cache/papers/`, `cache/index/`

---

## 8) Testing & evaluation

### Unit tests

- Citation marker parsing across styles
- Bibliography extraction correctness
- DOI/title matching and caching
- PDF chunk→page mapping integrity

### Integration tests

- End-to-end run on 2–3 sample theses with known ground truth pairs

### Evaluation metrics (research-grade, but start simple)

- For a labeled set of (span, ref) pairs:
  - Accuracy on {SUPPORTED/INSUFFICIENT/CONTRADICTED}
  - Precision/recall on “likely unsupported” detection
- Retrieval quality:
  - Recall@k of gold evidence chunk
- Calibration:
  - confidence vs. correctness (reliability curve)

### Acceptance criteria (MVP)

- Produces a report for a 100-page DOCX with ≥ 200 citation spans without crashing.
- For each span with a resolvable reference and available PDF, the report shows **at least one** evidence chunk with a **page number**.
- Clearly flags:
  - unresolved citations
  - missing full text
  - low-confidence assessments
- Report is usable offline when provided a local PDF corpus.

---

## 9) V2 roadmap (after MVP works)

- Better citation span detection with a trained model
- LaTeX-native support (parse `.aux`/`.bbl`/`.bib`)
- Multi-lingual support (DE/EN/FR/IT)
- Retraction checks + venue quality signals
- Supervisory workflows:
  - batch processing
  - comment export
  - student-facing “revision tasks” mode
- Pluggable models (swap retrieval/NLI) + benchmark suite
- Optional on-prem web app with authentication

---

## 10) Hard constraints & explicit failure modes

The system must explicitly label these situations rather than guessing:

- **Paywalled / no full text** → cannot validate claim; return `INSUFFICIENT_EVIDENCE` with reason
- **Citation scope ambiguous** → mark `ambiguous_span`
- **Reference cannot be resolved** → `unresolved_reference`
- **PDF parse fails** → `source_parse_error`

---

## 11) Deliverables checklist (what “done” means)

- [ ] CLI tool `cgcrv` with `analyze` command
- [ ] Local HTML report with filtering + evidence display
- [ ] JSON output matching data model sketch
- [ ] Caching for metadata + parsed papers + indexes
- [ ] Test suite (unit + 1 end-to-end sample)
- [ ] Documentation: install, offline mode, troubleshooting
