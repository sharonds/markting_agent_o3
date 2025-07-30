
# v3.2.2 micro-PR — generated 2025-07-30T00:50:27.487441Z

**What this adds**
- **Budget banner** in `SUMMARY.md` when spend exceeds `BUDGET_WARN_PCT * BUDGET_EUR` (default 80%).
- **Quality summary** in `SUMMARY.md` aggregating `qa_report.json` and `style_report.json`:
  - `qa_score`, `qa_failures`
  - `style_flags`, `avg_words_per_sentence`, `exclamations`, `passive_per_sentence`

**Env**
```bash
export BUDGET_EUR=8
export BUDGET_WARN_PCT=0.8
```

**Apply**
```bash
git checkout -b chore/v3.2.2
unzip -o v3.2.2-micro-PR.zip -d .
git add -A
git commit -m "v3.2.2: budget banner + quality summary in SUMMARY.md"
git push -u origin chore/v3.2.2
# open PR to main
```
