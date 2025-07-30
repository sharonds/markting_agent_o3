
import os, json
from typing import Dict, Any, List
from app.costs_tools import ToolCostLedger
from tools.search import SearchAdapter
from tools.keywords import KeywordAdapter

def _topn(lst, n):
    return lst[:n] if isinstance(lst, list) else []

def build_external_context(goal: str, artifacts_dir: str, top_sources: int = 6, top_keywords: int = 15) -> Dict[str, Any]:
    os.makedirs(artifacts_dir, exist_ok=True)
    ledger = ToolCostLedger(artifacts_dir)
    provider_search = os.getenv("PROVIDER_SEARCH", "none")
    provider_kw = os.getenv("PROVIDER_KEYWORDS", "llm")

    sa = SearchAdapter(artifacts_dir, ledger)
    sources = sa.search(provider_search, goal) or []

    seeds = [w for w in goal.split() if len(w) > 3][:10]
    ka = KeywordAdapter(artifacts_dir, ledger)
    kws = ka.enrich(provider_kw, seeds) or []

    sources = _topn(sources, int(os.getenv("TREATMENT_TOP_SOURCES", str(top_sources))))
    kws = _topn(kws, int(os.getenv("TREATMENT_TOP_KEYWORDS", str(top_keywords))))

    try:
        with open(os.path.join(artifacts_dir, "search_used.json"), "w", encoding="utf-8") as f:
            json.dump({"query": goal, "items": sources}, f, indent=2)
    except Exception:
        pass
    try:
        with open(os.path.join(artifacts_dir, "keywords_used.json"), "w", encoding="utf-8") as f:
            json.dump({"seeds": seeds, "items": kws}, f, indent=2)
    except Exception:
        pass

    lines = []
    if sources:
        lines.append("### External Sources (top)")
        for s in sources:
            title = s.get("title") or s.get("url")
            url = s.get("url")
            if url:
                lines.append(f"- {title} — {url}")
    if kws:
        lines.append("")
        lines.append("### Keyword Signals (top)")
        for k in kws:
            q = k.get("query")
            v = k.get("volume")
            cpc = k.get("cpc")
            comp = k.get("competition")
            parts = [f"volume={v}" if v is not None else None,
                     f"cpc={cpc}" if cpc is not None else None,
                     f"competition={comp}" if comp is not None else None]
            meta = ", ".join([p for p in parts if p])
            lines.append(f"- {q}" + (f": {meta}" if meta else ""))

    snippet = "\n".join(lines).strip()

    if snippet:
        with open(os.path.join(artifacts_dir, "external_context.md"), "w", encoding="utf-8") as f:
            f.write(snippet + "\n")

    return {
        "sources": sources,
        "keywords": kws,
        "snippet": snippet
    }
