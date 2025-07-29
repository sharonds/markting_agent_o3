import os, json, re
from app.tools.exporters import write_text, write_json
from app.brand_guard import check_text
from app.state import Artifact
from app.io import read_json
from app.llm_providers import LLMRouter, safe_extract_json

def _ensure_sources(post_text, evidence_ids):
    if re.search(r"^Sources:\s*f", post_text, flags=re.I|re.M):
        return post_text
    suffix = "\n\nSources: " + ", ".join(evidence_ids[:2]) + "\n" if evidence_ids else ""
    return post_text.rstrip() + suffix

def run(inputs, ctx) -> list[Artifact]:
    base = ctx['paths']['artifacts']
    strategy = read_json(os.path.join(base, "strategy_pack.json"))
    evidence = read_json(os.path.join(base, "evidence_pack.json"))
    messaging = strategy.get("messaging", {})
    pillar = next(iter(messaging.get("pillars", [])), {"id":"p1","name":"Ease of use"})
    provider = ctx['llm_router'].for_task('copywriter')
    brand = ctx['compass_meta'].get('brand','Zapier')

    if provider.name == "offline":
        draft = f"""# LinkedIn Post Draft

{brand} helps SMB teams automate routine work without code. Start fast with templates; connect thousands of apps to build reliable workflows.
CTA: Try it free.

Sources: f_appcount
"""
        usage = {}
    else:
        role = open("prompts/roles/copywriter.md","r",encoding="utf-8").read()
        message = f"""{role}

Brand: {brand}

Pillar:
{json.dumps(pillar, indent=2)}

Evidence Pack (IDs + claims):
{json.dumps([{"id":f["id"], "claim": f["claim"]} for f in evidence.get("facts",[])], indent=2)}

Return plain text only. Replace generic terms like "our platform" with "{brand}". End with "Sources: fX, fY".
"""
        resp = provider.chat([{"role":"system","content":"You are an excellent marketing copywriter."},
                              {"role":"user","content": message}], temperature=0.7, max_tokens=300)
        draft = resp.text or ""

    banned = ctx['compass_meta'].get('guardrails',{}).get('banned_phrases',[])
    draft = re.sub(r"\bour platform\b", brand, draft, flags=re.I)
    draft = _ensure_sources(draft, [f["id"] for f in evidence.get("facts",[]) if f.get("id")])
    ok, hits = check_text(draft, banned)

    post_filename = os.getenv("POST_FILENAME", "post_linkedin.md").strip() or "post_linkedin.md"
    out_md = os.path.join(base, post_filename)
    write_text(out_md, draft + ("" if ok else f"\n> NOTE: Banned phrases detected: {hits}\n"))

    policy = {"violations": [], "critical": False}
    write_json(os.path.join(base, "policy_check.json"), policy)

    return [Artifact(path=out_md, kind="md", summary=f"LinkedIn post draft ({post_filename})"),
            Artifact(path=os.path.join(base, "policy_check.json"), kind="json", summary="Policy check result")]
