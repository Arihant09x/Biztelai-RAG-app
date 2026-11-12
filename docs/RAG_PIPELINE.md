# BiztelAI Manufacturing SOP AI Copilot — RAG Pipeline Engineering

## 1. Structure-Aware PDF Extraction & Chunking
Standard chunking approaches that split documents blindly by token count break critical sequential steps in manufacturing SOPs and separate safety warnings from their parent procedures.

### Extraction Pipeline
1. **PyMuPDF (fitz)**:
   - Extracts structured text blocks with font-size metadata.
   - Identifies section headings based on font size differentials.
   - Extracts tables natively via `page.find_tables()` and converts them to Markdown tables.
2. **OCR Fallback**:
   - Detects scanned or low-text pages (`len(text.strip()) < 50`).
   - Automatically invokes `pytesseract` to extract embedded text.
3. **Structure-Aware Chunking Strategy**:
   - Target token count: ~700 tokens with ~100 token overlap.
   - Preserves section headings and page references.
   - Keeps safety alerts (`[SAFETY WARNING]`, `DANGER`, `MANDATORY PPE`) bound to the steps they protect.

---

## 2. Hybrid Retrieval Architecture
Query retrieval merges multiple candidate ranking streams using **Reciprocal Rank Fusion (RRF)**:

$$RRF\_Score(d) = \sum_{m \in M} \frac{1}{k + rank_m(d)}$$
where $k = 60$.

### Retrieval Streams:
1. **Dense Vector Search**: Sentence Transformers `all-MiniLM-L6-v2` (384 dimensions) with cosine distance. Captures conceptual and semantic intent.
2. **Full-Text Lexical Search**: PostgreSQL FTS with `to_tsvector` and `plainto_tsquery`. Captures exact part numbers, model designations, and technical terms.
3. **Exact Code Matcher**: Regular expression booster matching standard manufacturing tokens (e.g. `HP-200`, `SOP-101`, `480V`, `180 bar`, `0.02 mm`).

---

## 3. Cross-Encoder Reranking
Initial candidate chunks (top 10) are passed through a cross-encoder model (`cross-encoder/ms-marco-MiniLM-L-6-v2`):
- Unlike bi-encoders that encode query and document independently, the cross-encoder performs joint attention across the `(query, passage)` pair.
- Yields a calibrated relevance score.
- The pipeline filters results below the calibrated similarity threshold (`RAG_SIMILARITY_THRESHOLD`).

---

## 4. Context Engineering & Safety Abstention
The `ContextEngineeringService`:
1. Strips malicious prompt injection vectors (e.g. `"ignore previous instructions"`).
2. Maps each passage to an explicit citation handle: `source_1`, `source_2`.
3. Checks for contradictory instructions across different revisions or documents.
4. If relevance is insufficient or out-of-domain, the system **safely abstains** with an informative alert rather than fabricating answers.

