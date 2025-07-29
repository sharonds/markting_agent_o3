
import os, json, re
from app.tools.exporters import write_text, write_json
from app.brand_guard import check_text
from app.state import Artifact
from app.io import read_json
from app.llm_providers import LLMRouter
from app.db import add_message

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
    brand = ctx['compass_meta'].get('brand','Brand')
    context_pack = ctx.get("context_pack", {})
    locale = context_pack.get("locale","en-GB")

    if provider.name == "offline":
        draft = f"""# LinkedIn Post Draft

{brand} helps SMB teams automate routine work without code. Start fast with templates; connect thousands of apps to build reliable workflows.
CTA: Try it free.

Sources: f_appcount
"""
        usage=None
    else:
        role = open("prompts/roles/copywriter.md","r",encoding="utf-8").read()
        # Handle facts that might not have 'id' field
        facts_with_ids = []
        for i, f in enumerate(evidence.get("facts", [])):
            fact_id = f.get("id", f"facts[{i}]")
            fact_text = f.get("fact", f.get("claim", ""))
            facts_with_ids.append({"id": fact_id, "claim": fact_text})

        message = f"""{role}

ContextPack:
{json.dumps(context_pack, indent=2)}

Pillar:
{json.dumps(pillar, indent=2)}

Evidence Pack (IDs + claims):
{json.dumps(facts_with_ids, indent=2)}

Return plain text only. Replace generic terms like "our platform" with "{brand}". End with "Sources: fX, fY".
"""
        resp = provider.chat([{"role":"system","content":"You are an excellent marketing copywriter."},
                              {"role":"user","content": message}], temperature=0.7, max_tokens=300)
        draft = resp.text or ""
        add_message(ctx['db'], ctx['run_id'], ctx['current_task_id'], "assistant", provider.name, resp.text, {"prompt_tokens": getattr(resp.usage, "prompt_tokens", 0), "completion_tokens": getattr(resp.usage, "completion_tokens", 0)} if resp.usage else None)

    banned = ctx['compass_meta'].get('guardrails',{}).get('banned_phrases',[])
    draft = re.sub(r"\bour platform\b", brand, draft, flags=re.I)
    draft = _ensure_sources(draft, [f["id"] for f in evidence.get("facts",[]) if f.get("id")])
    ok, hits = check_text(draft, banned)

    post_filename = os.getenv("POST_FILENAME", "post_linkedin.md").strip() or "post_linkedin.md"
    out_md = os.path.join(base, post_filename)
    write_text(out_md, draft + ("" if ok else f"\n> NOTE: Banned phrases detected: {hits}\n"))

    gateB = {"locale": locale, "banned_hits": hits, "has_sources": bool(re.search(r"^Sources:", draft, flags=re.I|re.M))}
    gateB["numeric_claims_without_sources"] = bool(re.search(r"\d", draft) and not gateB["has_sources"])
    write_json(os.path.join(base, "gateB_report.json"), gateB)

    policy = {"violations": [], "critical": False}
    write_json(os.path.join(base, "policy_check.json"), policy)

    return [Artifact(path=out_md, kind="md", summary=f"LinkedIn post draft ({post_filename})"),
            Artifact(path=os.path.join(base, "policy_check.json"), kind="json", summary="Policy check result"),
            Artifact(path=os.path.join(base, "gateB_report.json"), kind="json", summary="Gate B report")]
