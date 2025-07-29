
# v3.2.1 tiny PR (generated 2025-07-29T23:34:56.685606Z)

Adds:
- Budget hard-stop: run aborts after any task if estimated spend (EUR) exceeds `BUDGET_EUR`.
- Style report: writes `artifacts/style_report.json` with sentence length, exclamations, ALL-CAPS ratio, passive voice heuristic.
- CI artifact upload: workflow now uploads `/out/**` as a downloadable artifact per run.

Usage:
```bash
export BUDGET_EUR=8
export COST_OPENAI_INPUT_PER1K=0.00
export COST_OPENAI_OUTPUT_PER1K=0.00
export COST_ANTHROPIC_INPUT_PER1K=0.00
export COST_ANTHROPIC_OUTPUT_PER1K=0.00
```
