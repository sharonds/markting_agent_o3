import json, os
from app.tools.exporters import write_json
from app.state import Artifact
from app.validation import validate_obj, load_schema
from app.io import read_yaml
from app.llm_providers import LLMRouter

def _offline_evidence(ctx):
    site = ctx['intake'].get('site','https://example.com')
    audience = ctx['intake'].get('audience','customers')
    obj = {
      "facts":[
        {"id":"f1","claim":f"{ctx['compass_meta'].get('brand','Acme')} reduces onboarding time for {audience}","source":site},
        {"id":"f2","claim":"Competitor Globex targets enterprises","source":"https://globex.example"}
      ],
      "competitors":[{"name":"Globex","positioning":"Enterprise-first automation","source":"https://globex.example"}],
      "keywords":[{"cluster":"beta launch","intent":"consideration","queries":["beta signup","early access"]},
                  {"cluster":"go-to-market","intent":"awareness","queries":["feature launch plan","saas launch checklist"]}],
      "risks":["Limited EU case studies"]
    }
    return obj

def run(inputs, ctx) -> list[Artifact]:
    task_id = ctx['current_task_id']
    prompts_dir = ctx['paths']['prompts']; responses_dir = ctx['paths']['responses']
    os.makedirs(prompts_dir, exist_ok=True); os.makedirs(responses_dir, exist_ok=True)

    provider = ctx['llm_router'].for_task('researcher')
    schema = load_schema("evidence_pack")

    if provider.name == "offline":
        obj = _offline_evidence(ctx)
    else:
        role = open("prompts/roles/researcher.md","r",encoding="utf-8").read()
        compass_excerpt = ctx['compass_body'][:1200]
        intake = ctx['intake']
        message = f"""{role}

Compass (excerpt):
{compass_excerpt}

Intake:
{json.dumps(intake, indent=2)}
Output STRICT JSON per schema 'evidence_pack'."""
        open(os.path.join(prompts_dir, f"{task_id}.txt"),"w",encoding="utf-8").write(message)
        resp = provider.json(
            [{"role":"system","content":"You are a precise research assistant."},
             {"role":"user","content": message}], schema=schema, temperature=0.2, max_tokens=900)
        open(os.path.join(responses_dir, f"{task_id}.txt"),"w",encoding="utf-8").write(resp.text or "")
        obj = resp.json_obj or {}
        if not obj:
            obj = _offline_evidence(ctx)

    errs = validate_obj("evidence_pack", obj)
    if errs:
        # Minimal repair fallback: guarantee keys
        obj.setdefault("facts", []); obj.setdefault("competitors", []); obj.setdefault("keywords", []); obj.setdefault("risks", [])
    out = os.path.join(ctx['paths']['artifacts'], "evidence_pack.json")
    write_json(out, obj)
    return [Artifact(path=out, kind="json", summary="Evidence pack")]
