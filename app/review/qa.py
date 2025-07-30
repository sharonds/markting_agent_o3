
import os, re, json
from typing import Dict, Any, List

def _read(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            if path.endswith(".json"):
                return json.load(f)
            return f.read()
    except Exception:
        return None

def _locale_warnings(text: str, locale: str) -> List[str]:
    if not text or not locale:
        return []
    warns = []
    if locale.lower().startswith("en-gb"):
        # very small sample; expand later as needed
        if "color" in text and "colour" not in text:
            warns.append("american_spelling_color_vs_colour")
        if "organize" in text and "organise" not in text:
            warns.append("american_spelling_organize_vs_organise")
    return warns

def generate_qa_report(artifacts_dir: str, context_pack: Dict[str, Any]) -> Dict[str, Any]:
    cp = context_pack or {}
    locale = (cp.get("locale") or "").lower()
    ctas_whitelist = cp.get("ctas") or []

    evidence = _read(os.path.join(artifacts_dir, "evidence_pack.json")) or {}
    strategy = _read(os.path.join(artifacts_dir, "strategy_pack.json")) or {}
    calendar = _read(os.path.join(artifacts_dir, "calendar.json")) or {"items":[]}
    gateA = _read(os.path.join(artifacts_dir, "gateA_report.json")) or {"coverage":[], "missing_total": 0, "low_quality":[]}
    gateB = _read(os.path.join(artifacts_dir, "gateB_report.json")) or {}
    post_filename = os.getenv("POST_FILENAME", "post_linkedin.md").strip() or "post_linkedin.md"
    post = _read(os.path.join(artifacts_dir, post_filename)) or ""

    checks = {}

    # 1) Evidence coverage (Gate A)
    missing_total = int(gateA.get("missing_total", 0) or 0)
    checks["evidence_coverage_ok"] = (missing_total == 0)

    # 2) Provenance average per pillar
    min_avg = float(os.getenv("PROVENANCE_MIN_AVG", "0.5"))
    low_quality = gateA.get("low_quality") or []
    checks["provenance_threshold_ok"] = (len(low_quality) == 0)

    # 3) Pillar coverage in calendar
    pillar_ids = [p.get("id") for p in (strategy.get("messaging",{}) or {}).get("pillars",[]) if p.get("id")]
    used_ids = [i.get("pillar_id") for i in (calendar.get("items") or []) if i.get("pillar_id")]
    missing_pillars = [pid for pid in pillar_ids if pid not in used_ids]
    checks["pillar_coverage_ok"] = (len(missing_pillars) == 0)

    # 4) CTA whitelist (only if whitelist provided)
    cta_ok = True
    bad_ctas = []
    if ctas_whitelist:
        for item in (calendar.get("items") or []):
            cta = (item.get("cta") or "").strip()
            if cta and cta not in ctas_whitelist:
                cta_ok = False
                bad_ctas.append({"date": item.get("date"), "channel": item.get("channel"), "cta": cta})
    checks["cta_whitelist_ok"] = cta_ok

    # 5) Post has Sources
    has_sources = bool(re.search(r"^Sources\s*:", post, flags=re.I|re.M))
    checks["post_has_sources"] = has_sources

    # 6) Numeric claims without sources (reuse gateB if present)
    numeric_without_sources = bool(re.search(r"\d", post) and not has_sources)
    gnum = gateB.get("numeric_claims_without_sources")
    if gnum is not None:
        numeric_without_sources = bool(gnum)
    checks["numeric_claims_cited"] = (not numeric_without_sources)

    # 7) Locale warnings (non-fatal)
    locale_warns = _locale_warnings(post, locale)

    # Score: simple ratio of passing checks (ignore locale warnings)
    total = len(checks)
    passed = sum(1 for v in checks.values() if v)
    score = round(passed / total, 3) if total else 1.0

    report = {
        "score": score,
        "checks": checks,
        "failures": [k for k, v in checks.items() if not v],
        "details": {
            "missing_total": missing_total,
            "low_quality": low_quality,
            "missing_pillars": missing_pillars,
            "bad_ctas": bad_ctas,
            "locale_warnings": locale_warns
        }
    }

    out_path = os.path.join(artifacts_dir, "qa_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return report
