"""Turn release notes into drafted doc updates.

For each release note: find the docs whose `features` overlap the release's `features`,
ask Claude to update each one (following the style guide and the product facts),
and write a review summary for the pull request. A person reviews every change before merge.

Usage:
    python scripts/update_docs.py releases/2026-11-04-v4.12.md [more release files] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from common import OUT, ROOT, STYLE_FILE, dump, load_docs, load_facts, parse

MODEL = "claude-opus-5-5"

SYSTEM = """You update help-center articles for a SaaS product after a release.
You get the style guide, the product facts (the source of truth), a release note and one current article.
Return the complete updated article body in Markdown, without frontmatter and without any commentary.
Change only what the release affects and keep everything else word for word.
If the release does not affect this article, return it unchanged.
Where something is unclear or the sources disagree, keep the current text and add an HTML comment starting with "REVIEW:" so the human reviewer sees it."""


def build_prompt(style: str, facts: dict, release: str, doc_name: str, doc_body: str) -> str:
    return (
        f"<style_guide>\n{style}\n</style_guide>\n\n"
        f"<product_facts>\n{json.dumps(facts, ensure_ascii=False, indent=2)}\n</product_facts>\n\n"
        f"<release_note>\n{release}\n</release_note>\n\n"
        f"<current_article name=\"{doc_name}\">\n{doc_body}\n</current_article>\n\n"
        "Return the updated article body."
    )


def draft_with_claude(prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY or an `ant auth login` profile
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",  # if the model declines, the API retries on a suitable fallback model
        output_config={"effort": "medium"},
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude declined to draft this update; edit the doc by hand.")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Draft was cut off (max_tokens); the article is too long for one request.")
    return "".join(block.text for block in response.content if block.type == "text").strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("releases", nargs="+", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="write the prompts to out/prompts/ instead of calling Claude")
    args = parser.parse_args()

    style = STYLE_FILE.read_text(encoding="utf-8")
    facts = load_facts()
    docs = load_docs()
    summary = ["## Drafted doc updates", "", "Drafted by Claude from the release notes below. **Review every change before merging.**", ""]
    changed = 0

    for release_path in args.releases:
        release_path = (ROOT / release_path) if not release_path.is_absolute() else release_path
        release_text = release_path.read_text(encoding="utf-8")
        meta, _ = parse(release_text)
        version, features = meta.get("version", "?"), set(meta.get("features", []))
        summary.append(f"### Release {version} (`{release_path.name}`)")

        affected = [(p, m, b) for p, m, b in docs if features & set(m.get("features", []))]
        if not affected:
            summary.append("- No docs are tagged with these features. Does this release need a new article?")
        for path, doc_meta, body in affected:
            prompt = build_prompt(style, facts, release_text, path.name, body)
            if args.dry_run:
                target = OUT / "prompts" / f"{version}-{path.stem}.md"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(SYSTEM + "\n\n" + prompt, encoding="utf-8")
                summary.append(f"- `{path.name}`: prompt written to `{target.relative_to(ROOT).as_posix()}`")
                continue
            new_body = draft_with_claude(prompt)
            if new_body.strip() == body.strip():
                summary.append(f"- `{path.name}`: no change needed")
                continue
            doc_meta["last_release"] = version
            doc_meta["last_reviewed"] = "pending"
            path.write_text(dump(doc_meta, new_body), encoding="utf-8")
            flags = new_body.count("REVIEW:")
            note = f", **{flags} point(s) flagged for review**" if flags else ""
            summary.append(f"- `{path.name}`: updated{note}")
            changed += 1
        summary.append("")

    summary += [
        "### Reviewer checklist",
        "- [ ] Every UI label and limit matches `product/facts.json` and the live product",
        "- [ ] Steps work when followed in the product",
        "- [ ] Screenshots and in-app tours for these features are still correct",
        "- [ ] Style guide followed",
        "- [ ] Any mistake found is logged in `rules/review-log.md` (and a rule added if it can recur)",
        "- [ ] `last_reviewed` set to today's date in each approved doc",
        "",
        f"_Generated {date.today().isoformat()}_",
    ]
    OUT.mkdir(exist_ok=True)
    (OUT / "review-summary.md").write_text("\n".join(summary), encoding="utf-8")
    print("\n".join(summary))
    print(f"\n{changed} doc(s) updated. Summary in out/review-summary.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
