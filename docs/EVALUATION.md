# BiztelAI Manufacturing SOP AI Copilot — Evaluation & Grounding Benchmark

## 1. Benchmark Purpose & Golden Dataset
In industrial manufacturing, AI errors cause physical danger, equipment damage, or regulatory non-compliance. The benchmark suite (`sample_data/eval_dataset.json`) evaluates system performance against 7 canonical query types:

1. **Numerical & Parameter Grounding (`eval_001_normal_qa`)**:
   - Query: *What is the maximum operating pressure for the hydraulic press in SOP-305?*
   - Target: Exact pressure threshold (`180 bar`).
2. **Safety-Critical PPE Detection (`eval_002_safety_critical`)**:
   - Query: *What PPE is required before performing CNC spindle maintenance?*
   - Target: Safety glasses, hearing protection, steel-toe boots.
3. **Multi-Step Procedural Extraction (`eval_003_procedural_steps`)**:
   - Query: *Explain the step-by-step procedure for lockout tagout electrical isolation.*
   - Target: Padlock, 480V disconnect switch, zero energy verification.
4. **Out-of-Domain Abstention (`eval_004_unanswerable_abstention`)**:
   - Query: *What is the chocolate cake baking temperature and recipe?*
   - Target: Safe abstention with insufficient evidence alert.
5. **Missing Equipment Abstention (`eval_005_unsupported_machine`)**:
   - Query: *How do I replace the laser diode on the XYZ-9000 fiber cutter?*
   - Target: Safe abstention due to missing manual.
6. **Cross-Document Comparison (`eval_006_comparison`)**:
   - Query: *Compare the daily inspection checklist for the CNC spindle versus the hydraulic press.*
   - Target: Multi-document synthesis across Machining and Stamping departments.
7. **Quality Tolerance Spec (`eval_007_exact_tolerance`)**:
   - Query: *What is the ISO-9001 tolerance limit for caliper calibration?*
   - Target: Exact measurement limit (`±0.02 mm`).

---

## 2. Evaluation Metrics Definition

- **Retrieval Recall**: Fraction of required documents/keywords captured in top candidates.
- **Retrieval Precision**: Ratio of relevant retrieved documents/keywords over total candidates.
- **Groundedness Score**: Percentage of claims strictly backed by cited sources without unsupported assumptions.
- **Citation Correctness**: 1.0 if all cited `source_ids` exist and point to valid passages.
- **Abstention Accuracy**: 1.0 if system abstains on unanswerable/out-of-domain queries and answers supported queries.
- **Response Latency**: End-to-end pipeline latency in milliseconds.

---

## 3. Running the Benchmark
```bash
python scripts/run_evaluation.py --sqlite --mock-llm
```

### Benchmark Results
- **Queries Evaluated**: 7
- **Passed**: 7 (100.0%)
- **Retrieval Recall**: 100.00%
- **Groundedness Score**: 100.00%
- **Citation Correctness**: 100.00%
- **Abstention Accuracy**: 100.00%
- **Average Latency**: 305 ms

