
# PR-A: Cross-run memory (SQLite) — generated 2025-07-30T00:06:37.593589Z

**What this adds**
- SQLite memory store that persists facts, segments, pillars across runs.
- Loads Memory Snapshot at start → `artifacts/memory_snapshot.json`; injects `memory_stats` into ContextPack.
- Upserts from artifacts on finish → `artifacts/memory_persist_report.json`.

**Env**
- `MEMORY_DB_PATH` (default `memory.sqlite`)
- `MEMORY_READ` (default `1`), `MEMORY_WRITE` (default `1`)

**Apply**
```bash
git checkout -b chore/pr-a-memory
unzip -o pr-a-memory-bundle.zip -d .
git add -A
git commit -m "PR-A: cross-run SQLite memory + prompt integration"
git push -u origin chore/pr-a-memory
# open PR to main
```
