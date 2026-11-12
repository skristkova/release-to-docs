"""Shared helpers: paths, a tiny frontmatter parser, version comparison."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = ROOT / "out"
FACTS_FILE = ROOT / "product" / "facts.json"
STYLE_FILE = ROOT / "rules" / "style-guide.md"

_FM = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.S)


def parse(text: str) -> tuple[dict, str]:
    """Split a Markdown file into (frontmatter dict, body). Supports `key: value` and `key: [a, b]`."""
    m = _FM.match(text.replace("\r\n", "\n"))
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        if value.startswith("[") and value.endswith("]"):
            meta[key] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
        else:
            meta[key] = value
    return meta, m.group(2)


def dump(meta: dict, body: str) -> str:
    lines = [f"{k}: [{', '.join(v)}]" if isinstance(v, list) else f"{k}: {v}" for k, v in meta.items()]
    return "---\n" + "\n".join(lines) + "\n---\n\n" + body.lstrip("\n")


def load_docs() -> list[tuple[Path, dict, str]]:
    return [(p, *parse(p.read_text(encoding="utf-8"))) for p in sorted(DOCS.glob("*.md"))]


def load_facts() -> dict:
    return json.loads(FACTS_FILE.read_text(encoding="utf-8"))


def version_key(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", str(v)))
