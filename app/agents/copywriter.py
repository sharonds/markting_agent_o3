import os, json
from app.tools.exporters import write_text, write_json
from app.brand_guard import check_text
from app.state import Artifact
from app.io import read_json
from app.llm_providers import LLMRouter, safe_extract_json

def _offline_post(pillar_name):
    return f"""# LinkedIn Post Draft

We're opening Beta access for SMB SaaS founders.
If speed to value matters, you'll like this: plan your launch in a week, with strategy guardrails baked in.
CTA: Join early access today.

Sources: f1
"""

def _policy_check(provider, text):
    if provider.name == "offline":
        return {"violations": [], "critical": False}
    prompt = f"""Check the following text for policy violations. Return JSON with fields:
- violations: list of strings
- critical: boolean

Text:
{text}
"""
    resp = provider.chat([{"role":"system","content":"You are a compliance checker. Output JSON only when possible."},
                          {"role":"user","content": prompt}], temperature=0.0, max_tokens=200)
    obj = safe_extract_json(resp.text) or {"violations": [], "critical": False}
    return obj

def run(inputs, ctx) -> list[Artifact]:
    base = ctx['paths']['artifacts']
    strategy = read_json(os.path.join(base, "strategy_pack.json"))
    messaging = strategy.get("messaging", {})
    pillar = next(iter(messaging.get("pillars", [])), {"id":"p1","name":"Speed"})
    provider = ctx['llm_router'].for_task('copywriter')
    # Build prompt if using a real model
    if provider.name == "offline":
        draft = _offline_post(pillar.get("name","Speed"))
        usage = {}
    else:
        evidence = read_json(os.path.join(base, "evidence_pack.json"))
        role = open("prompts/roles/copywriter.md","r",encoding="utf-8").read()
        message = f"""{role}

Pillar:
{json.dumps(pillar, indent=2)}

Evidence Pack (IDs + claims):
{json.dumps([{"id":f["id"], "claim": f["claim"]} for f in evidence.get("facts",[])], indent=2)}

Return plain text only.
"""
        prompt_path = os.path.join(ctx['paths']['prompts'], f"{ctx['current_task_id']}.txt")
        with open(prompt_path,"w",encoding="utf-8") as f: f.write(message)
        resp = provider.chat([{"role":"system","content":"You are an excellent marketing copywriter."},
                              {"role":"user","content": message}], temperature=0.7, max_tokens=300)
        draft = resp.text or _offline_post(pillar.get("name","Speed"))
        usage = resp.usage

    banned = ctx['compass_meta'].get('guardrails',{}).get('banned_phrases',[])
    ok, hits = check_text(draft, banned)
    policy = _policy_check(provider, draft)

    out_md = os.path.join(base, "post_linkedin.md")
    write_text(out_md, draft + ("" if ok else f"\n> NOTE: Banned phrases detected: {hits}\n"))

    out_policy = os.path.join(base, "policy_check.json")
    write_json(out_policy, policy)

    return [Artifact(path=out_md, kind="md", summary="LinkedIn post draft"),
            Artifact(path=out_policy, kind="json", summary="Policy check result")]
