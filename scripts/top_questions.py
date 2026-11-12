"""Rank what customers ask about most, and point each topic at the doc that should answer it.

Reads data/tickets.csv (columns: ticket_id, created, topic, question) and writes out/top-questions.md.
Topics without a doc are the first candidates for a new article.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict

from common import OUT, ROOT, load_docs


def main() -> int:
    with open(ROOT / "data" / "tickets.csv", encoding="utf-8", newline="") as f:
        tickets = list(csv.DictReader(f))

    counts = Counter(t["topic"] for t in tickets)
    examples: dict[str, list[str]] = defaultdict(list)
    for t in tickets:
        if len(examples[t["topic"]]) < 3:
            examples[t["topic"]].append(t["question"])

    doc_for = {}
    for path, meta, _ in load_docs():
        for feature in meta.get("features", []):
            doc_for.setdefault(feature, path.name)

    lines = [
        "# Most-asked topics",
        "",
        f"{len(tickets)} tickets analysed.",
        "",
        "| Rank | Topic | Tickets | Share | Doc | Example questions |",
        "|---|---|---|---|---|---|",
    ]
    for rank, (topic, n) in enumerate(counts.most_common(), start=1):
        doc = f"`{doc_for[topic]}`" if topic in doc_for else "**no doc yet**"
        lines.append(f"| {rank} | {topic} | {n} | {n / len(tickets):.0%} | {doc} | {'; '.join(examples[topic])} |")

    OUT.mkdir(exist_ok=True)
    (OUT / "top-questions.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
