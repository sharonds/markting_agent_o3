
# v3.2.2-hotfix — generated 2025-07-30T01:18:17.093534Z

Restores **PR-D routing & budget checks** and keeps **PR-C QA** while preserving v3.2.2 additions (budget banner + quality section in `SUMMARY.md`).

**What changed**
- `app/orchestrator/core.py` only:
  - Re-add `load_routing/apply_env` and write `artifacts/routing_resolved.json`.
  - Keep QA generation after Gate B.
  - Use `select id, role from tasks` for role mapping.
  - Keep v3.2.2 Budget banner + Quality section in `SUMMARY.md`.

**Apply**
```bash
git checkout -b chore/v3.2.2-hotfix
unzip -o v3.2.2-hotfix.zip -d .
git add app/orchestrator/core.py README-v3.2.2-hotfix.md
git commit -m "v3.2.2-hotfix: restore routing+QA; keep budget banner & quality section"
git push -u origin chore/v3.2.2-hotfix
# open PR to main
```
