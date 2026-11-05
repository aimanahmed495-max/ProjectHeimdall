---
name: ai-log
description: Draft the AI usage log entry for today's session (prompt, output, human review, verification). Use when asked for the AI log, session log, or usage log.
---
# Draft the AI usage log

1. Read `.ai-log/raw/<today>.jsonl` (today = local date). If missing, reconstruct from this conversation and say so at the top.
2. Run `git log --since=midnight --oneline` and `git branch --show-current` to see what actually shipped.
3. Group raw events into exchanges. Drop trivial ones (typo fixes, "continue", reruns).
4. Write `docs/ai-log/<today>.md`. One entry per exchange, matching the course template:

   ### <HH:MM> <short title>
   - **Date:** <today>
   - **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
   - **Tool used:** Cursor or Claude Code
   - **Associated Git issue:** `#N` if known, otherwise `TODO (Aiman)`
   - **Branch:** current branch
   - **Prompt submitted:** quote or tight summary
   - **AI output summary:** one or two sentences
   - **Human review and modifications:** what was kept, changed, or rejected and why. If the user did not state it, write `TODO (Aiman)`. Never invent a decision.
   - **Verification:** only commands that were actually run in this session and their results (for example `bash scripts/check` passed). If nothing was run, write `Not verified`.

5. Top of file: `Status: DRAFT, needs Aiman's review`. Plain language, no filler.
6. Do not edit `AI_USAGE_LOG.md`. Do not commit unless the task says to. Tell the user the file path and how many TODOs remain.
