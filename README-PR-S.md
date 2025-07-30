
# PR-S: External tool foundation — search & keywords adapters + rate-limit/caching + tool cost ledger (shadow mode) — 2025-07-30T02:15:18.070544Z

**What this adds (no behavior change)**
- Pluggable **search** adapter (`tools/search.py`) with **Perplexity** option and a `none` fallback.
- Pluggable **keywords** adapter (`tools/keywords.py`) with **DataForSEO** option and an LLM fallback.
- **Rate limiting + retries** and a **file cache (TTL)** for external calls.
- **Tool cost ledger** → `artifacts/tool_usage.json` (aggregated `by_tool` + `total_eur`).
- **Shadow mode** (set `SHADOW=1`): calls adapters using the run **goal**, writes **`search_shadow.json`** / **`keywords_shadow.json`**, but **does not** change agent prompts yet.

**Environment** (only if you turn providers on)
```bash
# Search
export PROVIDER_SEARCH=perplexity       # or: none
export PERPLEXITY_API_KEY=***
export PERPLEXITY_MODEL=sonar
export SEARCH_REGION=EU
export SEARCH_LANG=en-GB
export SEARCH_CACHE_TTL_DAYS=3
export SEARCH_MAX_RESULTS=8
export SEARCH_MAX_CONCURRENCY=4

# Keywords
export PROVIDER_KEYWORDS=dataforseo     # or: llm
export DATAFORSEO_LOGIN=***
export DATAFORSEO_PASSWORD=***
export KEYWORD_CACHE_TTL_DAYS=7
export KEYWORD_MAX_CONCURRENCY=2

# Costs (override placeholder EUR values)
export COST_PERPLEXITY_PER_CALL_EUR=0.002
export COST_DATAFORSEO_PER_CALL_EUR=0.01

# Cache & shadow
export SHADOW=1
export CACHE_DIR=.cache
export CACHE_BUST=0
```

**Apply**
```bash
git checkout -b chore/pr-s-adapters
unzip -o pr-s-adapters-bundle.zip -d .
git add -A
git commit -m "PR-S: search/keyword adapters + rate-limit/caching + tool cost ledger (shadow mode)"
git push -u origin chore/pr-s-adapters
# open PR to main
```

**Smoke test (shadow mode)**
```bash
export PYTHONPATH=.
export AUTO_APPROVE=1
export SHADOW=1
export PROVIDER_SEARCH=none           # safe default
export PROVIDER_KEYWORDS=llm          # safe default
python app/main.py --goal "PR-S shadow test"

# Should see (if SHADOW=1):
ls out/*/artifacts/search_shadow.json || echo "no search (provider=none)"
ls out/*/artifacts/keywords_shadow.json || echo "no keywords (provider=llm)"
ls out/*/artifacts/tool_usage.json
```

**Next PR (S1b)** will connect adapters into the **Researcher** prompts (treatment variant) so we can A/B with **PR-X**.
