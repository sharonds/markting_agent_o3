
import json, os
from app.tools.exporters import write_json
from app.state import Artifact
from app.validation import validate_obj, load_schema
from app.llm_providers import LLMRouter
from app.llm_utils import attempt_json
from app.db import add_message

def _offline_evidence(ctx):
    site = ctx['intake'].get('site','https://example.com')
    audience = ctx['intake'].get('audience','customers')
    obj = {
      "facts":[
        {"id":"f_appcount","claim":f"{ctx['compass_meta'].get('brand','Brand')} connects with 8,000+ apps (official site).","source":"https://zapier.com/apps","geo":"Global"},
        {"id":"f1","claim":f"{ctx['compass_meta'].get('brand','Brand')} reduces onboarding time for {audience}","source":site,"geo":"EU"}
      ],
      "competitors":[{"name":"Make","positioning":"Visual, scenario-based automation","source":"https://www.make.com"}],
      "keywords":[{"cluster":"automation templates","intent":"awareness","queries":["Zapier templates","no-code workflow templates"]}],
      "risks":["Limited EU case studies"]
    }
    return obj

def run(inputs, ctx) -> list[Artifact]:
    task_id = ctx['current_task_id']
    provider = ctx['llm_router'].for_task('researcher')
    schema = load_schema("evidence_pack")
    context_pack = ctx.get("context_pack", {})

    if provider.name == "offline":
        obj = _offline_evidence(ctx); usage=None
    else:
        role = open("prompts/roles/researcher.md","r",encoding="utf-8").read()
        message = f"""{role}

ContextPack:
{json.dumps(context_pack, indent=2)}

Return a single top-level JSON object matching schema 'evidence_pack'. No code fences. No wrapper keys.
"""
        messages=[{"role":"system","content":"You are a precise research assistant."},{"role":"user","content": message}]
        obj, resp = attempt_json(provider, "evidence_pack", messages, schema, temperature=0.2, max_tokens=900)
        usage = getattr(resp, "usage", None)
        add_message(ctx['db'], ctx['run_id'], task_id, "assistant", provider.name, resp.text, usage)

    out = os.path.join(ctx['paths']['artifacts'], "evidence_pack.json")
    write_json(out, obj)
    return [Artifact(path=out, kind="json", summary="Evidence pack")]
