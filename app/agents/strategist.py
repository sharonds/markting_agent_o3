import json, os
from app.tools.exporters import write_json, write_text
from app.state import Artifact
from app.validation import validate_obj, load_schema
from app.io import read_json
from app.llm_providers import LLMRouter

def _offline_strategy(evidence):
    return {
      "icp": {"segments": [{
        "name":"SMB SaaS founders (EU)",
        "jobs":["ship faster","generate MQLs"],
        "pains":["thin marketing bandwidth"],
        "gains":["predictable pipeline"],
        "triggers":["launching new feature"],
        "qualifiers":["team <25","self-serve motion"],
        "disqualifiers":["enterprise sales cycles >9m"]
      }]},
      "positioning":{
        "category":"Agentic marketing co-pilot",
        "for":"SMB SaaS founders in EU",
        "who":"need to launch features fast without a big team",
        "our_product":"Acme",
        "is_a":"workflow + content generator with strategy guardrails",
        "unlike":"Globex (enterprise-first) and Contoso (copy-only tools)",
        "we":"tie ICP/positioning to every asset via gating and citations",
        "rtbs":[{"text":"7-day launch pack","evidence_ids":["f1"]}]
      },
      "messaging":{"pillars":[
        {"id":"p1","name":"Speed to value","claims":["From intake to launch in 7 days"],"evidence_ids":["f1"],"tones":["confident","practical"],"ctas":["Book a 15-min fit check"]},
        {"id":"p2","name":"Practical guidance","claims":["No fluff; concrete steps"],"evidence_ids":["f2"],"tones":["helpful"],"ctas":["See a sample pack"]},
        {"id":"p3","name":"Social proof","claims":["Proof > promises"],"evidence_ids":["f1"],"tones":["credible"],"ctas":["Read a case note"]}
      ]}
    }

def run(inputs, ctx) -> list[Artifact]:
    task_id = ctx['current_task_id']
    provider = ctx['llm_router'].for_task('strategist')
    schema = load_schema("strategy_pack")
    evidence = read_json(os.path.join(ctx['paths']['artifacts'], "evidence_pack.json"))
    if provider.name == "offline":
        obj = _offline_strategy(evidence)
    else:
        role = open("prompts/roles/strategist.md","r",encoding="utf-8").read()
        message = f"""{role}

Evidence Pack (JSON):
{json.dumps(evidence, indent=2)[:4000]}

Output STRICT JSON per schema 'strategy_pack'. Also create a short 'positioning.md' summary (title + positioning statement)."""
        open(os.path.join(ctx['paths']['prompts'], f"{task_id}.txt"),"w",encoding="utf-8").write(message)
        resp = provider.json([{"role":"system","content":"You are a rigorous strategist producing JSON outputs."},
                              {"role":"user","content": message}], schema=schema, temperature=0.3, max_tokens=900)
        open(os.path.join(ctx['paths']['responses'], f"{task_id}.txt"),"w",encoding="utf-8").write(resp.text or "")
        obj = resp.json_obj or {}
        if not obj:
            obj = _offline_strategy(evidence)
    errs = validate_obj("strategy_pack", obj)
    # write artifacts
    base = ctx['paths']['artifacts']
    write_json(os.path.join(base,"strategy_pack.json"), obj)
    # simple positioning.md render
    pos_text = f"# Positioning (One-Pager)\n\n**Category**: {obj['positioning'].get('category')}\n\n**Statement**: Unlike {obj['positioning'].get('unlike')}, we {obj['positioning'].get('we')}."
    write_text(os.path.join(base,"positioning.md"), pos_text + "\n")
    return [Artifact(path=os.path.join(base,"strategy_pack.json"), kind="json", summary="Strategy pack"),
            Artifact(path=os.path.join(base,"positioning.md"), kind="md", summary="Positioning one-pager")]
