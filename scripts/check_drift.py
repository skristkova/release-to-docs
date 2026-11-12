"""Flag docs that have drifted from the product.

Checks every doc against product/facts.json:
  - renamed or removed UI labels still used in the text
  - docs whose features changed in a newer release than the doc last covered
  - docs still waiting for human review

Exits with 1 when anything is found, so CI shows it. Writes out/drift-report.md.
"""
from __future__ import annotations

import re
import sys

from common import OUT, load_docs, load_facts, version_key


def main() -> int:
    facts = load_facts()
    renamed = facts.get("renamed_ui_labels", {})
    removed = facts.get("removed_ui_labels", [])
    feature_releases = facts.get("feature_releases", {})
    issues: list[str] = []

    for path, meta, body in load_docs():
        name = path.name
        for old, new in renamed.items():
            if re.search(rf"\*\*{re.escape(old)}\*\*|\b{re.escape(old)}\b", body):
                issues.append(f"`{name}`: uses old label **{old}**; the product now says **{new}**")
        for label in removed:
            if label in body:
                issues.append(f"`{name}`: mentions **{label}**, which no longer exists")

        covered = meta.get("last_release", "0")
        for feature in meta.get("features", []):
            changed_in = feature_releases.get(feature)
            if changed_in and version_key(changed_in) > version_key(covered):
                issues.append(f"`{name}`: covers release {covered}, but `{feature}` changed in {changed_in}")

        if meta.get("last_reviewed") == "pending":
            issues.append(f"`{name}`: drafted update still waiting for human review")

    report = ["# Drift report", ""] + ([f"- {i}" for i in issues] if issues else ["No drift found."])
    OUT.mkdir(exist_ok=True)
    (OUT / "drift-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
