# Style guide

These rules go to Claude with every draft. When review finds a mistake that could happen again, add a rule here and log it in `review-log.md`.

## Voice
- Write for a busy admin, not an engineer. Plain words, short sentences.
- Address the reader as "you". Use the present tense.
- One idea per paragraph.

## Steps
- A task is a numbered list. Aim for five steps or fewer; if it needs more, split the task.
- Each step starts with a verb: "Go to", "Click", "Choose".
- Put UI labels in **bold**, exactly as they appear in the product. Use `→` for menu paths.

## Facts
- Take every UI label, limit and plan name from `product/facts.json`. If the release note and the facts file disagree, keep the current text and add `<!-- REVIEW: ... -->` explaining the conflict.
- Say which plans a feature is on when it isn't on every plan.
- Never invent a setting, limit or button that isn't in the release note, the current doc or the facts file.

## Scope of an update
- Change only what the release affects. Keep the rest of the article word for word.
- If a new feature needs its own task, add a new `##` section; don't rewrite existing ones.

## Rules added from review
- R1 (2026-10-21): Retention and limits always come as a table per plan, never inline in a sentence.
- R2 (2026-10-28): When a UI element moves, describe the new location only. No "previously it was…".
