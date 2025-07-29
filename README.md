
# v3.2 PR bundle (generated 2025-07-29T21:55:50.087205Z)

Includes:
- ContextPack (locale/audience/geos/channels/timeline/ctas) → injected into every agent
- Schemas extended: evidence facts (geo/date), ICP objections, calendar (format/cta)
- Planner: rule-first slots from timeline/channels with pillar/intent coverage
- Gate A/B reports: evidence coverage; locale/CTA/numeric checks
- Cost tracking (token-based; set env rates COST_* to enable EUR totals)
- Tests for context pack & reports

Apply:
```bash
git checkout -b chore/v3.2
unzip -o v3.2-pr-bundle.zip -d .
git add -A
git commit -m "v3.2: ContextPack, planner, gate reports, costs"
git push -u origin chore/v3.2
# open PR to main
```

Env for costs (optional):
```bash
export COST_OPENAI_INPUT_PER1K=0.00
export COST_OPENAI_OUTPUT_PER1K=0.00
export COST_ANTHROPIC_INPUT_PER1K=0.00
export COST_ANTHROPIC_OUTPUT_PER1K=0.00
```
