# Sprint 4A: The Evaluation Engine & Ground Truth

**Goal:** Establish a deterministic baseline for measuring AI performance by implementing the Evaluation Engine and a curated Ground Truth dataset.

## 🎯 Deliverables

1.  **Ground Truth Dataset (`/evaluation/dataset.json`):**
    *   Manually curate a JSON dataset of at least 5 documents with "expected" structured outputs.
    *   Fields: `company_name`, `invoice_id`, `amount`, `due_date`, `status`.

2.  **The `IEvaluator` Port:**
    *   Define the interface in `src/bdis/ports/evaluator.py`.
    *   Methods: `evaluate(extracted_data: dict, expected_data: dict) -> EvaluationResult`.

3.  **The Evaluator Adapter:**
    *   Implement `evaluation/evaluator.py` (implementing `IEvaluator`).
    *   Logic: Compare fields, calculate accuracy scores, and identify missing/incorrect fields.

4.  **TDD Foundation:**
    *   Create `tests/test_evaluation/test_evaluator.py`.
    *   Ensure >90% coverage on the evaluation logic.

## ✅ Definition of Done
- A `pytest` run shows the Evaluator correctly identifying mismatches in a dummy dataset.
- The `dataset.json` is successfully loaded and parsed by the engine.
- No direct coupling between the Evaluator and any AI clients.
