
# PR-S1b: Treatment wiring — inject external sources/keywords into context_pack (variant=treatment) — 2025-07-30T04:00:07.338355Z

**What this does**
- Adds `app/adapters/context_enrichment.py` to call Perplexity/DataForSEO (through existing adapters) and build a compact snippet.
- When `variant=treatment`, orchestrator enriches `context_pack` with:
  - `external_sources`: top URLs from search
  - `keyword_signals`: enriched keyword rows
  - `external_context_snippet`: a small, readable block for prompts
- Writes artifacts: `external_context.md`, `search_used.json`, `keywords_used.json`.
- **Baseline runs unchanged.** Only treatment gets the extra context.

**Env**
```bash
export VARIANT=treatment
export PROVIDER_SEARCH=perplexity
export PERPLEXITY_API_KEY=...

export PROVIDER_KEYWORDS=dataforseo
export DATAFORSEO_LOGIN=...
export DATAFORSEO_PASSWORD=...
# Optional knobs
export TREATMENT_TOP_SOURCES=6
export TREATMENT_TOP_KEYWORDS=15
```

**Apply**
```bash
git checkout -b chore/pr-s1b-treatment-wiring
unzip -o pr-s1b-treatment-wiring.zip -d .
git add -A
git commit -m "PR-S1b: inject external sources/keywords into context_pack for treatment variant"
git push -u origin chore/pr-s1b-treatment-wiring
# open PR to main
```

**A/B with the harness**
```bash
python tools/exp_runner.py   --experiment-id search_adapter_v1   --scenario zapier_eu_smb   --goal "Launch beta for EU SMB founders"   --iterations 5 --auto-approve
```
