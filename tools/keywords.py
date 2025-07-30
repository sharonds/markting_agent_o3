
import os, json, requests, hashlib
from typing import List, Dict, Any, Optional
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

    def _cache_key(self, provider: str, seeds: list) -> str:
        key = "|".join(sorted(seeds))[:512]
        return "kw:" + hashlib.sha1(f"{provider}|{key}".encode("utf-8")).hexdigest()

    def enrich(self, provider: str, seed_terms: List[str]) -> List[Dict[str, Any]]:
        provider = (provider or "llm").lower().strip()
        if provider == "dataforseo":
            return self._dataforseo_search_volume(seed_terms)
        # fallback (no external calls)
        return [{"query": s, "volume": None, "cpc": None, "competition": None} for s in seed_terms]

    def _dataforseo_search_volume(self, seed_terms: List[str]) -> List[Dict[str, Any]]:
        """Call DataForSEO Google Ads Search Volume (live)."""
        login = os.getenv("DATAFORSEO_LOGIN")
        password = os.getenv("DATAFORSEO_PASSWORD")
        if not (login and password):
            return [{"query": s, "volume": None, "cpc": None, "competition": None} for s in seed_terms]

        seeds = [s for s in seed_terms if s] or []
        if not seeds:
            return []

        # Cache
        ck = self._cache_key("dataforseo", seeds)
        cached = cache_get(ck, self.cache_ttl)
        if cached is not None:
            return cached

        # Build payload (array of task objects, per docs)
        # https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live/
        task: dict = {}
        loc_code = os.getenv("DATAFORSEO_LOCATION_CODE")
        loc_name = os.getenv("DATAFORSEO_LOCATION_NAME")
        lang_code = os.getenv("DATAFORSEO_LANGUAGE_CODE")
        lang_name = os.getenv("DATAFORSEO_LANGUAGE_NAME")
        if loc_code:
            try: task["location_code"] = int(loc_code)
            except Exception: pass
        elif loc_name:
            task["location_name"] = loc_name
        if lang_code:
            task["language_code"] = lang_code
        elif lang_name:
            task["language_name"] = lang_name
        task["keywords"] = seeds[:1000]

        url = os.getenv(
            "DATAFORSEO_ENDPOINT",
            "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live",
        )

        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        def do():
            resp = requests.post(
                url,
                auth=(login, password),
                json=[task],
                headers=headers,
                timeout=45,
            )
            resp.raise_for_status()
            return resp.json()

        data = self.limiter.call(do)

        # Validate DataForSEO payload structure
        if data.get("status_code") != 20000:
            # Write shadow for debugging
            try:
                with open(os.path.join(self.artifacts_dir, "keywords_shadow.json"), "w", encoding="utf-8") as f:
                    json.dump({"provider": "dataforseo", "request": [task], "raw": data}, f, indent=2)
            except Exception:
                pass
            raise RuntimeError(f"DataForSEO error: {data.get('status_code')} {data.get('status_message')}")

        items: List[Dict[str, Any]] = []
        for t in data.get("tasks", []):
            for r in (t.get("result") or []):
                items.append({
                    "query": r.get("keyword"),
                    "location_code": r.get("location_code"),
                    "language_code": r.get("language_code"),
                    "volume": r.get("search_volume"),
                    "cpc": r.get("cpc"),
                    "competition": r.get("competition"),
                    "monthly_searches": r.get("monthly_searches", []),
                })

        # Shadow artifact + cost
        try:
            with open(os.path.join(self.artifacts_dir, "keywords_shadow.json"), "w", encoding="utf-8") as f:
                json.dump({"provider": "dataforseo", "request": [task], "items": items}, f, indent=2)
        except Exception:
            pass
        self.ledger.add("dataforseo", calls=1)
        cache_set(ck, items)
        return items
