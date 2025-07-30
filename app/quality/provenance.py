
import os, re, time
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from datetime import datetime
from typing import Tuple, Dict, Any, List

# Lazy import requests so tests without internet don't fail on import
def _requests():
    import requests
    return requests

UTM_PREFIX = ("utm_", "_hs", "fbclid", "gclid")

TRUSTED_HOSTS = set([
    "zapier.com", "developers.google.com", "learn.microsoft.com",
    "aws.amazon.com", "cloud.google.com", "openai.com", "anthropic.com"
])

TLD_TRUST = {
    "gov": 1.0,
    "edu": 0.9,
    "org": 0.7,
    "com": 0.6,
}

def normalize_url(url: str) -> Tuple[str, str]:
    try:
        u = urlparse(url.strip())
        scheme = u.scheme.lower() or "https"
        netloc = u.netloc.lower()
        path = re.sub(r"/+$", "", u.path)  # strip trailing slash
        # drop tracking params
        q = [(k, v) for (k, v) in parse_qsl(u.query, keep_blank_values=False) if not k.lower().startswith(UTM_PREFIX)]
        query = urlencode(q)
        normalized = urlunparse((scheme, netloc, path, "", query, ""))
        host = netloc.split(":")[0]
        return normalized, host
    except Exception:
        return url, ""

def head_check(url: str, timeout: float = None) -> Tuple[bool, int, str]:
    timeout = timeout or float(os.getenv("PROVENANCE_TIMEOUT_SECS", "3"))
    try:
        r = _requests().head(url, allow_redirects=True, timeout=timeout)
        return (r.status_code < 400, r.status_code, r.url)
    except Exception:
        return (False, 0, url)

def _host_trust(host: str) -> float:
    if not host:
        return 0.0
    if host in TRUSTED_HOSTS:
        return 0.9
    tld = host.split(".")[-1]
    return TLD_TRUST.get(tld, 0.5)

def _recency_score(date_str: str) -> float:
    if not date_str:
        return 0.6  # neutral if unknown
    try:
        d = datetime.fromisoformat(date_str)
        years = max(0.0, (datetime.utcnow() - d).days / 365.0)
        if years <= 1: return 1.0
        if years <= 2: return 0.85
        if years <= 3: return 0.7
        if years <= 5: return 0.5
        return 0.3
    except Exception:
        return 0.5

def score_fact(f: Dict[str, Any]) -> float:
    host = f.get("host","")
    reachable = f.get("reachable", False)
    date = f.get("date")
    s_host = _host_trust(host)           # 0..1
    s_reach = 1.0 if reachable else 0.2  # reachable matters
    s_age = _recency_score(date)         # 0.3..1.0
    # weights: host 0.4, reachable 0.4, age 0.2
    score = 0.4*s_host + 0.4*s_reach + 0.2*s_age
    return round(min(max(score, 0.0), 1.0), 3)

def enhance_evidence(evidence: Dict[str, Any], link_check: bool = True) -> Dict[str, Any]:
    timeout = float(os.getenv("PROVENANCE_TIMEOUT_SECS", "3"))
    # allow disabling link checks in CI/tests
    perform = link_check and os.getenv("PROVENANCE_LINK_CHECK","1") != "0"
    seen = set()
    new_facts: List[Dict[str, Any]] = []
    for f in evidence.get("facts", []):
        src = f.get("source") or f.get("source_url") or ""
        canon, host = normalize_url(src)
        f["canonical_url"] = canon
        f["host"] = host
        if perform and canon:
            ok, status, final_url = head_check(canon, timeout)
        else:
            ok, status, final_url = (True, 200, canon) if canon else (False, 0, canon)
        f["reachable"] = bool(ok)
        f["status_code"] = int(status)
        # simple dedupe key: same claim text + host
        claim_key = re.sub(r"\s+", " ", (f.get("claim") or f.get("fact") or "")).strip().lower()
        dedupe_key = (claim_key, host)
        f["provenance_score"] = score_fact(f)
        if dedupe_key in seen:
            # keep the higher scored variant
            # if current score > previous stored, replace the earlier one
            # naive approach: append and filter at end; for simplicity, skip duplicates here
            continue
        seen.add(dedupe_key)
        new_facts.append(f)
    evidence["facts"] = new_facts
    return evidence
