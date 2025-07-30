
# PR-D: Routing table + 80% budget warning + per-task cost breakdown — generated 2025-07-30T00:44:22.397426Z

**What this adds**
- **Routing table** (`config/routing.yml`) to choose provider per role (researcher/strategist/content_planner/copywriter). Defaults provided.
- **Resolved routing** is written to `artifacts/routing_resolved.json`, and env vars `LLM_<ROLE>` & `TEMP_<ROLE>` are set for compatibility.
- **80% budget warning**: when `estimated_spend_eur >= 0.8 * BUDGET_EUR`, we log `budget_warning` and write `artifacts/budget_warning.json` (non-fatal).
- **Per-task cost breakdown** in `SUMMARY.md` under `## Cost` with `total_estimated_eur`, `budget_utilization`, and `by_role`.

**Usage**
- Edit `config/routing.yml` to change providers/temps.
- Set a budget (EUR): `export BUDGET_EUR=8` (works with the hard stop introduced in v3.2.1).

**Apply**
```bash
git checkout -b chore/pr-d-routing
unzip -o pr-d-routing-bundle.zip -d .
git add -A
git commit -m "PR-D: routing table, 80% budget warning, per-role cost breakdown"
git push -u origin chore/pr-d-routing
# open PR to main
```
