#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '.')

# Test with providers that create shadow files
os.environ["SHADOW"] = "1"
os.environ["PROVIDER_SEARCH"] = "perplexity"  # Will create shadow (even without API key)
os.environ["PROVIDER_KEYWORDS"] = "dataforseo"  # Will create shadow (even without credentials)

from app.costs_tools import ToolCostLedger
from tools.search import SearchAdapter
from tools.keywords import KeywordAdapter

artifacts_dir = "test_shadow_providers"
os.makedirs(artifacts_dir, exist_ok=True)

goal = "PR-S shadow test"
ledger = ToolCostLedger(artifacts_dir)

# Test search with perplexity (should create shadow even without API key)
sa = SearchAdapter(artifacts_dir, ledger)
result = sa.search("perplexity", goal)
print(f"Search results: {len(result) if result else 0}")

# Test keywords with dataforseo (should create shadow even without credentials)
seeds = ["PR-S", "shadow", "test"]
ka = KeywordAdapter(artifacts_dir, ledger)
result2 = ka.enrich("dataforseo", seeds)
print(f"Keyword results: {len(result2) if result2 else 0}")

# Check for files
import glob
files = glob.glob(f"{artifacts_dir}/*")
for f in files:
    print(f"Created: {f}")
