
# PR-X: Experiment harness (A/B + metrics) — generated 2025-07-30T01:51:31.908294Z

**What this adds**
- **Experiment metadata** per run: `artifacts/experiment.json` with `experiment_id`, `variant`, `scenario`, `run_number`.
- **Metrics artifact** per run: `artifacts/metrics.json` aggregating research, strategy, QA/style, and cost stats (LLM + tools).
- **Offline A/B runner**: `tools/exp_runner.py` to execute paired baseline/treatment runs with constant settings and emit a CSV + Markdown summary.
- **Canary sampling**: if you set `EXPERIMENT_FRACTION`, the orchestrator will auto-assign `baseline|treatment` per run (hash-stable) when `VARIANT` isn't set.

**Env flags**
- `EXPERIMENT_ID` (string), `VARIANT` (`baseline|treatment`), `SCENARIO` (string), `RUN_NUMBER` (int).
- `EXPERIMENT_FRACTION` (0..1): % of runs going to treatment (only if `VARIANT` unset).
- Existing: `AUTO_APPROVE`, `BUDGET_*`, routing, etc.

**Apply**
```bash
git checkout -b chore/pr-x-experiment
unzip -o pr-x-experiment-bundle.zip -d .
git add -A
git commit -m "PR-X: experiment harness (experiment.json + metrics.json + exp_runner.py)"
git push -u origin chore/pr-x-experiment
# open PR to main
```

**Run a quick A/B (local)**
```bash
python tools/exp_runner.py   --experiment-id search_adapter_v1   --scenario zapier_eu_smb   --goal "Launch beta for EU SMB founders"   --iterations 3 --auto-approve
```

Artifacts will be under `out/experiments/` (CSV + MD) and each run will have `artifacts/experiment.json` and `artifacts/metrics.json`.
