# Orvina: always-on agent instructions

These rules apply to every message in every session, in addition to `prompts/_RULES.md`.

## Checkpoints (mandatory)

`docs/PROGRESS.md` is the only memory of this project. A new session must be able to continue from it alone. If it does not exist, create it with the template below before doing anything else.

**At the start of every session:** read `docs/PROGRESS.md` first, then say in one line which phase and task you are continuing and the next step written there.

**Write a checkpoint:**
1. after every numbered task in a phase prompt, before starting the next task;
2. after every 3 files you create or change, even in the middle of a task;
3. before any command that may take longer than 2 minutes (install, build, Docker, deploy, e2e);
4. when a test or build fails, with the error, before you try to fix it;
5. at the end of every phase, followed by the phase report;
6. whenever the user writes "checkpoint" or "simpan";
7. before you end your reply, every time.

A checkpoint is not done until `docs/PROGRESS.md` is saved. Never write "I will update the progress later".

**How to write one:**
- Replace the whole "Current phase" section.
- Add new lines to "Done", "Not done / blocked" and "Checkpoint log". Never delete old lines there.
- Keep each checkpoint short (5–10 lines). No secrets, no token values, no full file contents.

## Template for `docs/PROGRESS.md`

```markdown
# Orvina progress

## Current phase
- Phase: P<n> <name>
- Task: <n> of <total>, <task name>
- Status: in progress | blocked | done
- Last change: <files changed, one line>
- Next step: <one exact action a new session can do immediately>

## Done
- P<n> task <n>: done, <short note>

## Not done / blocked
- P<n> task <n>: <what>, <reason>, <what is needed>

## Assumptions

## Manual checks for the developer

## Checkpoint log
- <YYYY-MM-DD HH:MM> · <model ID> · P<n> task <n> · <what changed> · tests: <pass / fail / not run> · next: <next step>

## Prompt log
- <YYYY-MM-DD> · P<n> · <model ID> · prompt: <file name> · summary · fixes · test output · screenshots
```

## Evidence
- Every checkpoint and prompt-log line names the exact model you are running on (one of `zai-org/GLM-5.2`, `deepseek-ai/DeepSeek-V4-Pro-0813`, `stepfun-ai/Step-3.5-Flash`, `Qwen/Qwen3.8-27B`). If you are running on any other model, stop and tell the user before writing code.
- Screenshots go in `docs/evidence/screenshots/` and are listed in the prompt log.
