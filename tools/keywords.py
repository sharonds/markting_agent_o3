
import os, json, requests, hashlib
from typing import List, Dict, Any
from app.util.file_cache import get as cache_get, set as cache_set
from app.util.rate_limit import RateLimiter
from app.costs_tools import ToolCostLedger

class KeywordAdapter:
    def __init__(self, artifacts_dir: str, ledger: ToolCostLedger):
        self.artifacts_dir = artifacts_dir
        self.ledger = ledger
        self.ttl_days = int(os.getenv("KEYWORD_CACHE_TTL_DAYS", "7"))
        self.cache_ttl = self.ttl_days * 86400
        self.limiter = RateLimiter(int(os.getenv("KEYWORD_MAX_CONCURRENCY", "2")))

    def _cache_key(self, provider: str, seed: str) -> str:
        return "kw:" + hashlib.sha1(f"{provider}|{seed}".encode("utf-8")).hexdigest()

    def enrich(self, provider: str, seed_terms: List[str]) -> List[Dict[str, Any]]:
        provider = (provider or "llm").lower().strip()
        if provider == "dataforseo":
            return self._dataforseo(seed_terms)
        # fallback (no external calls)
        return [{"query": s, "volume": None, "cpc": None, "difficulty": None} for s in seed_terms]

    def _dataforseo(self, seed_terms: List[str]) -> List[Dict[str, Any]]:
        u = os.getenv("DATAFORSEO_LOGIN")
        p = os.getenv("DATAFORSEO_PASSWORD")
        if not (u and p):
            return [{"query": s, "volume": None, "cpc": None, "difficulty": None} for s in seed_terms]

        # This is a placeholder; integrate with DataForSEO API v3 as needed
        # We'll simulate one call cost entry and write a shadow artifact.
        self.ledger.add("dataforseo", calls=1)
        payload = [{"query": s, "volume": 0, "cpc": 0.0, "difficulty": 0.0} for s in seed_terms]

        try:
            outp = os.path.join(self.artifacts_dir, "keywords_shadow.json")
            with open(outp, "w", encoding="utf-8") as f:
                json.dump({"provider": "dataforseo", "items": payload}, f, indent=2)
        except Exception:
            pass
        return payload
