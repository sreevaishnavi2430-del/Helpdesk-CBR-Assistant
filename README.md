# Case-Based Reasoning System for Intelligent IT Helpdesk Ticket Resolution

A small, local helpdesk assistant that retrieves similar solved tickets using TF-IDF and cosine similarity, proposes a solution when confidence is sufficient, and learns from staff feedback by retaining reviewed cases in SQLite.

## Run

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

The app initializes `data/helpdesk.db` from `data/sample_tickets.csv` on first run. The starter dataset is synthetic demonstration data, not a real support-ticket corpus.

## Workflow

1. Describe the issue, optionally select a category, then retrieve the three closest cases.
2. Review similarity scores and the recommended solution. Low-confidence matches are explicitly routed to manual handling.
3. Mark the suggestion as worked or not worked. Add a corrected resolution where appropriate; reviewed outcomes are retained as new cases.
4. Review case-base size and category counts in the sidebar.

## Evaluate

Run `python evaluate.py` to perform a deterministic stratified train/test retrieval evaluation over the starter dataset and print top-1/top-3 accuracy. The evaluation holds out cases from retrieval, then ranks only the training cases. This is a small synthetic demonstration; use a labeled, representative dataset for meaningful results. Evaluation uses the category as the expected match label and only makes sense when each category has multiple examples.

## Project layout

- `app.py` – Streamlit user interface and CBR feedback flow
- `cbr.py` – SQLite storage, text retrieval, confidence handling
- `evaluate.py` – held-out top-1/top-3 evaluation
- `data/sample_tickets.csv` – synthetic starter cases

## Notes

- Default confidence threshold: 0.20. Tune it against labeled validation data before operational use.
- Category filtering is optional; without it, retrieval searches the full case base.
- TF-IDF is intentionally the baseline. Sentence embeddings can be added behind the retrieval interface after evaluation.
