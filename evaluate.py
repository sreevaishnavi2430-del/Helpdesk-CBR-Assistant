"""Deterministic held-out top-k retrieval evaluation for the sample cases."""
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from cbr import CaseBase

DATA = Path(__file__).parent / "data" / "sample_tickets.csv"

def main():
    df = pd.read_csv(DATA).fillna("")
    stratify = df.category if df.category.value_counts().min() >= 2 else None
    train, test = train_test_split(df, test_size=0.25, random_state=42, stratify=stratify)
    # SQLite's shared in-memory URI lets each short-lived connection use the same database.
    base = CaseBase(Path("file:helpdesk_eval?mode=memory&cache=shared"))
    with base._connect() as conn:
        conn.execute("DELETE FROM cases")
    for row in train.itertuples(index=False):
        base.add_case(str(row.problem), str(row.category), str(row.solution), str(row.success).lower() not in ("false", "0", "no"), "evaluation")
    top1 = top3 = 0
    for row in test.itertuples(index=False):
        ranked = base.retrieve(str(row.problem), top_k=3)
        labels = [m.category for m in ranked]
        top1 += bool(labels and labels[0] == row.category)
        top3 += row.category in labels
    n = len(test)
    print(f"Evaluation cases: {n}")
    print(f"Top-1 category retrieval accuracy: {top1 / n:.3f}")
    print(f"Top-3 category retrieval accuracy: {top3 / n:.3f}")
    print("Metric: whether the retrieved case category matches the held-out ticket category.")

if __name__ == "__main__":
    main()
