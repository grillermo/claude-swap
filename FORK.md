# Fork

This repository (`github`, [grillermo/claude-swap](https://github.com/grillermo/claude-swap))
is a fork of [realiti4/claude-swap](https://github.com/realiti4/claude-swap)
(`upstream`). This file records how the fork brings in upstream commits without losing its
own features, and where the last sync stopped.

- Remote `upstream` is upstream (`https://github.com/realiti4/claude-swap`).
- Remote `github` is the fork (`git@github.com:grillermo/claude-swap.git`).
- The fork's branch is `main`; upstream's is `main`.
- Fork point: `9aa6d029` (2026-09-20, "Merge pull request #364 from BarganConstantin/fix/update-check-prerelease").

**Pointed at this file with no other task, sync the fork: follow [Syncing](#syncing) end to end.**

## What the fork adds, and must keep

Every fork feature a sync must protect, with where it lives (files, settings keys, tests)
so a sync can confirm it survived. When an upstream commit would break one, keep the fork's behavior
and adapt the upstream change around it.

- **`storage.backupKeychain` setting** (`e2c28318`): with it off
  (`cswap config set storage.backupKeychain false`), cswap's per-account backups and their `.prev`
  generation are read and written only as `.enc` files under `credentials/`, as on Linux, so nothing
  on the backup path calls `security` and a locked Keychain or a Background (SSH/tmux) session can
  no longer leave the backup behind the live token. Claude Code's own Keychain items are still read.
  Default stays on. Lives in `src/claude_swap/settings.py` (`StorageSettings.backup_keychain`, the
  `storage` / `backupKeychain` entry in the config-key table, the `settings.json` parser),
  `src/claude_swap/credentials.py` (the backup read/write paths that consult it), and the tests
  `tests/test_backup_keychain_setting.py`, `tests/test_config_cli.py`, `tests/test_settings.py`.
  After a merge, check that every backup read/write path upstream added or rewrote in
  `credentials.py` still honors the setting.
- **Tooling**: this `FORK.md`.

When the fork gains a feature, add it here in the same commit, so the next sync knows to protect it.

## What the fork does not carry

Nothing yet: the fork has not dropped or reverted anything from upstream.

## Syncing

The goal is the most upstream possible: every upstream commit lands, and the fork bends to fit it.
`main` is published on `github`, so sync by **merging**, never by rebasing or force-pushing.

1. **Start clean.** `git status` must be clean on `main`. Run
   `git fetch --multiple upstream github`, and make sure `main` is not behind
   `github/main`. Remove a `sync-upstream` branch or `.worktrees/sync-upstream` left
   from an earlier sync, once `git merge-base --is-ancestor sync-upstream main` confirms
   `main` already holds it.
2. **Survey.** List what is coming with
   `git log --oneline main..upstream/main`, and what the fork holds
   with `git log --oneline --no-merges upstream/main..main`. Read
   [Upstream commits left out](#upstream-commits-left-out) first. Note upstream commits that touch
   the areas in [What the fork adds](#what-the-fork-adds-and-must-keep) (`settings.py`,
   `credentials.py`): that is where conflicts and silent breakage will be.
3. **Merge in a worktree.**
   `git worktree add .worktrees/sync-upstream -b sync-upstream main`, then
   `git merge upstream/main` there.
4. **Resolve conflicts toward upstream.** Take upstream's version of anything the fork did not
   deliberately change. Where upstream rewrote something the fork changed, re-express the fork's
   feature in upstream's new shape; never revert or pin upstream code to keep the old shape.
   Generated files: for `uv.lock`, take upstream's and run `uv lock` if the fork's
   `pyproject.toml` differs. Keep `pyproject.toml`'s version upstream's.
5. **Check the merge did not quietly break a feature.** A clean merge is not proof. For each item
   in [What the fork adds](#what-the-fork-adds-and-must-keep), confirm its code, settings keys and
   tests survived, and that upstream did not add a second path that bypasses it.
6. **Pass the definition of done**: `uv sync --locked` then `uv run pytest` (what upstream's CI
   runs), all green. Fix failures with follow-up commits on `sync-upstream`, each explaining which
   upstream change it adapts the fork to.
7. **Only as a last resort, leave an upstream commit out**: when it cannot coexist with a fork
   feature even after adapting. `git revert` that one commit on `sync-upstream`, say why in the
   message, and add a row to [Upstream commits left out](#upstream-commits-left-out).
8. **Land it.** Fast-forward `main` to `sync-upstream`
   (`git -C /Users/grillermo/c/claude-swap merge --ff-only sync-upstream`), then remove the
   worktree and branch.
9. **Fix any doc the sync made wrong**, this one included.
10. **Report and stop**: how many upstream commits came in, every conflict and how it was resolved,
    every follow-up adaptation, anything reverted, and the test and build results. Ask before
    pushing to `github` and before installing or deploying anything.

## Upstream commits left out

Every upstream commit the fork reviewed and decided not to take, and why. A sync reads this first.
Anything not listed here comes in. A revert survives later merges, but upstream follow-ups to a
listed commit will conflict, so judge them against its reason. To take a commit later, revert the
revert and delete the row.
Revisit an entry when the conflict may be gone.

| Upstream | Date | Upstream subject | Conflicts with | Why it is left out | Decided |
|---|---|---|---|---|---|

## Issue reviews

Upstream ranges already searched for a fix to a specific problem. Before searching again for the
same problem, only look at upstream commits newer than the recorded boundary:

```bash
git log --reverse --no-merges --format='%h %ad %an %s' --date=short --abbrev=8 <LAST_REVIEWED_SHA>..upstream/main
```

None recorded yet. Add a `### <problem>` subsection per review, with the date, the last reviewed
upstream hash, the conclusion, and a table of the commits whose diffs were read (hashes without
backticks).
