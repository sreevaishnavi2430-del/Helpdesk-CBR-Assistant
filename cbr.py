"""
Core case base and retrieval logic for the IT helpdesk CBR demo.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "helpdesk.db"
CSV_PATH = ROOT / "data" / "sample_tickets.csv"
DEFAULT_THRESHOLD = 0.20

@dataclass
class Match:
    case_id: int
    problem: str
    category: str
    solution: str
    success: bool
    score: float

class CaseBase:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        conn = sqlite3.connect(str(self.db_path), uri=str(self.db_path).startswith("file:"))
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self):
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem TEXT NOT NULL,
                category TEXT NOT NULL,
                solution TEXT NOT NULL,
                success INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                source TEXT NOT NULL DEFAULT 'seed'
            )""")
            count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        if count == 0 and self.db_path.resolve() == DB_PATH.resolve() and CSV_PATH.exists():
            self.import_csv(CSV_PATH)

    def import_csv(self, path: Path = CSV_PATH):
        df = pd.read_csv(path).fillna("")
        with self._connect() as conn:
            conn.executemany(
                "INSERT INTO cases(problem, category, solution, success, source) VALUES (?, ?, ?, ?, 'seed')",
                [(str(r.problem).strip(), str(r.category).strip() or "General",
                  str(r.solution).strip(), int(str(r.success).lower() not in ("false", "0", "no")))
                 for r in df.itertuples(index=False) if str(r.problem).strip() and str(r.solution).strip()]
            )

    def add_case(self, problem: str, category: str, solution: str, success: bool, source: str = "feedback") -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO cases(problem, category, solution, success, source) VALUES (?, ?, ?, ?, ?)",
                (problem.strip(), category.strip() or "General", solution.strip(), int(success), source),
            )
            return int(cur.lastrowid)

    def all_cases(self) -> list[dict]:
        with self._connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM cases ORDER BY id DESC")]

    def categories(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT DISTINCT category FROM cases ORDER BY category")
            return [r[0] for r in rows]

    def retrieve(self, query: str, category: str | None = None, top_k: int = 3) -> list[Match]:
        query = query.strip()
        if not query:
            return []
        cases = self.all_cases()
        if category:
            cases = [c for c in cases if c["category"] == category]
        if not cases:
            return []
        corpus = [c["problem"] for c in cases]
        # Character n-grams handle short ticket text and spelling variation reasonably well.
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), analyzer="word", sublinear_tf=True, strip_accents="unicode")
        try:
            matrix = vectorizer.fit_transform(corpus + [query])
        except ValueError:
            return []
        scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
        ranked = sorted(zip(scores, cases), key=lambda item: (item[0], item[1]["success"], item[1]["id"]), reverse=True)
        return [Match(int(c["id"]), c["problem"], c["category"], c["solution"], bool(c["success"]), float(s))
                for s, c in ranked[:top_k]]

    @staticmethod
    def recommendation(matches: Iterable[Match], threshold: float = DEFAULT_THRESHOLD) -> tuple[Match | None, bool]:
        best = next(iter(matches), None)
        return best, bool(best and best.success and best.score >= threshold)


