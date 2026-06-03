---
description: After finishing a task — append a DEVLOG entry, commit all changes, and push to main. Use when the user says they're done, asks to ship/log/commit, or invokes /ship.
user-invocable: true
---

The user has finished a task and wants to log it, commit, and push. Do the following steps in order:

## Step 1 — Write the DEVLOG entry

Append a new entry to `.claude/DEVLOG.md` at the top (below the `# Project Dev Log` header and `---` separator, above all existing entries). Use this exact format:

```
---

**Task:** One-line description of what needed doing
**Solution:** What was changed and why. Name specific functions. Explain design choices when non-obvious.
**Date:** YYYY-MM-DD
```

- Use today's date.
- Infer the task and solution from the conversation context and recent file changes. If the task isn't clear from context, ask the user for a one-line summary before proceeding.
- The solution should name specific functions/files changed and explain non-obvious design decisions — not just restate the task.
- Keep it factual and concise (2–5 sentences). Match the tone and detail level of existing entries.

## Step 2 — Commit

Run `git status` and `git diff` to see what changed, then stage and commit all modified files. Write a commit message that summarizes the change (not the DEVLOG entry — the actual code change). Follow the existing commit message style in `git log`.

Stage specific files by name (not `git add -A`). Include the DEVLOG.md update in the same commit.

## Step 3 — Push

Push to the `main` branch:

```
git push origin main
```

Confirm the push succeeded and report the final commit hash to the user.
