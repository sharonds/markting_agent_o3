
import os, json, hashlib, requests
from typing import List, Dict, Any
from urllib.parse import urlparse
from app.util.file_cache import get as cache_get, set as cache_set
from app.util.rate_limit import RateLimiter
from app.costs_tools import ToolCostLedger

class SearchAdapter:
    def __init__(self, artifacts_dir: str, ledger: ToolCostLedger):
        self.artifacts_dir = artifacts_dir
        self.ledger = ledger
        self.ttl_days = int(os.getenv("SEARCH_CACHE_TTL_DAYS", "3"))
        self.cache_ttl = self.ttl_days * 86400
        self.max_results = int(os.getenv("SEARCH_MAX_RESULTS", "8"))
        self.region = os.getenv("SEARCH_REGION", "EU")
        self.lang = os.getenv("SEARCH_LANG", "en-GB")
        self.limiter = RateLimiter(int(os.getenv("SEARCH_MAX_CONCURRENCY", "4")))

    def _cache_key(self, provider: str, query: str) -> str:
        payload = json.dumps({"provider": provider, "q": query, "region": self.region, "lang": self.lang}, sort_keys=True)
        return "search:" + hashlib.sha1(payload.encode("utf-8")).hexdigest()

    def search(self, provider: str, query: str) -> List[Dict[str, Any]]:
        provider = (provider or "none").lower().strip()
        if provider == "none":
            return []
        if provider == "perplexity":
            return self._search_perplexity(query)
        # add more providers here
        return []

    def _search_perplexity(self, query: str) -> List[Dict[str, Any]]:
        ck = self._cache_key("perplexity", query)
        cached = cache_get(ck, self.cache_ttl)
        if cached is not None:
            return cached

        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            return []

        model = os.getenv("PERPLEXITY_MODEL", "sonar")
        url = os.getenv("PERPLEXITY_ENDPOINT", "https://api.perplexity.ai/chat/completions")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        # Using an OpenAI-compatible chat payload; adjust to provider spec if needed
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": f"You are a research assistant. Return concise sources with titles and URLs for the query. Region={self.region}, lang={self.lang}"},
                {"role": "user", "content": query}
            ],
            "max_tokens": 600
        }
        def do():
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()

        data = self.limiter.call(do)
        # Extract structured search results from Perplexity response
        items: List[Dict[str, Any]] = []
        try:
            # First, try to get structured search_results
            if "search_results" in data and data["search_results"]:
                for result in data["search_results"][:self.max_results]:
                    if "url" in result:
                        items.append({
                            "title": result.get("title", urlparse(result["url"]).netloc),
                            "url": result["url"],
                            "date": result.get("date"),
                            "last_updated": result.get("last_updated")
                        })
            
            # If no search_results, fallback to citations array
            elif "citations" in data and data["citations"]:
                for url in data["citations"][:self.max_results]:
                    if url:
                        items.append({
                            "title": urlparse(url).netloc,
                            "url": url
                        })
            
            # Last fallback: regex extraction from content
            elif "choices" in data and data["choices"]:
                content = data["choices"][0]["message"]["content"]
                import re
                urls = re.findall(r"https?://\S+", content)
                seen = set()
                for u in urls:
                    if u in seen: continue
                    seen.add(u)
                    parsed = urlparse(u)
                    items.append({"title": parsed.netloc, "url": u})
                    if len(items) >= self.max_results:
                        break
        except Exception:
            items = []

        cache_set(ck, items)
        # add cost entry
        self.ledger.add("perplexity", calls=1)
        # write shadow artifact
        try:
            outp = os.path.join(self.artifacts_dir, "search_shadow.json")
            with open(outp, "w", encoding="utf-8") as f:
                json.dump({"provider": "perplexity", "query": query, "results": items}, f, indent=2)
        except Exception:
            pass
        return items
