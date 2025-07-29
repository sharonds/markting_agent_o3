
import json, os
from app.tools.exporters import write_json, write_text
from app.state import Artifact
from app.validation import validate_obj, load_schema
from app.io import read_json
from app.llm_providers import LLMRouter
from app.db import add_message

def _offline_strategy(evidence, context_pack):
    brand = context_pack.get("brand","Brand")
    return {
      "icp": {"segments": [{
        "name":"SMB SaaS founders (EU)",
        "jobs":["ship faster","generate MQLs"],
        "pains":["thin marketing bandwidth"],
        "gains":["predictable pipeline"],
        "triggers":["launching new feature"],
        "qualifiers":["team <25","self-serve motion"],
        "disqualifiers":["enterprise sales cycles >9m"],
        "objections":["No time to set up","We lack technical skills","Is it reliable?"]
      }]},
      "positioning":{
        "category":"No-code automation platform",
        "for":"SMB teams",
        "who":"need to automate workflows quickly without engineers",
        "our_product": brand,
        "is_a":"workflow + template library with reliability and breadth",
        "unlike":"complex, developer-first integration suites",
        "we":"connect 8,000+ apps and turn repetitive tasks into reliable workflows",
        "rtbs":[{"text":"8,000+ apps catalog","evidence_ids":["f_appcount"]}]
      },
      "messaging":{"pillars":[
        {"id":"p1","name":"Ease of use","claims":["Start fast with templates"],"evidence_ids":["f_appcount"],"tones":["friendly","clear"],"ctas":["Explore templates"]},
        {"id":"p2","name":"Time savings","claims":["Automate repetitive work"],"evidence_ids":["f1"],"tones":["practical"],"ctas":["Try it free"]},
        {"id":"p3","name":"Breadth & reliability","claims":["Works across your stack"],"evidence_ids":["f_appcount"],"tones":["credible"],"ctas":["See popular zaps"]}
      ]}
    }

def run(inputs, ctx) -> list[Artifact]:
    base = ctx['paths']['artifacts']
    provider = ctx['llm_router'].for_task('strategist')
    schema = load_schema("strategy_pack")
    evidence = read_json(os.path.join(base, "evidence_pack.json"))
    context_pack = ctx.get("context_pack", {})

    if provider.name == "offline":
        obj = _offline_strategy(evidence, context_pack); usage=None
    else:
        role = open("prompts/roles/strategist.md","r",encoding="utf-8").read()
        message = f"""{role}

ContextPack:
{json.dumps(context_pack, indent=2)}

Evidence Pack (JSON):
{json.dumps(evidence, indent=2)[:4000]}

Return a single top-level JSON object matching schema 'strategy_pack'. No code fences. No wrapper keys.
"""
        messages=[{"role":"system","content":"You are a rigorous strategist producing JSON outputs."},
                  {"role":"user","content": message}]
        try:
            resp = provider.json(messages, schema, temperature=0.3, max_tokens=1500)
            obj = resp.json_obj
            usage = {"prompt_tokens": getattr(resp.usage, "prompt_tokens", 0), "completion_tokens": getattr(resp.usage, "completion_tokens", 0)} if resp.usage else None
            add_message(ctx['db'], ctx['run_id'], ctx['current_task_id'], "assistant", provider.name, resp.text, usage)
        except Exception as e:
            print(f"ERROR: Strategist LLM call failed: {e}")
            raise

    # Validate the object has required keys
    if not obj:
        raise ValueError("Strategy pack object is None or empty")
    
    if 'positioning' not in obj:
        raise ValueError(f"Strategy pack missing required 'positioning' key. Got keys: {list(obj.keys())}")
    
    validate_obj("strategy_pack", obj)

    write_json(os.path.join(base,"strategy_pack.json"), obj)
    pos_text = f"# Positioning (One-Pager)\n\n**Category**: {obj['positioning'].get('category')}\n\n**Statement**: Unlike {obj['positioning'].get('unlike')}, {obj['positioning'].get('our_product')} helps {context_pack.get('audience','teams')} automate work quickly—connecting 8,000+ apps to turn repetitive tasks into reliable workflows (see evidence f_appcount)."
    write_text(os.path.join(base,"positioning.md"), pos_text + "\n")
    return [Artifact(path=os.path.join(base,"strategy_pack.json"), kind="json", summary="Strategy pack"),
            Artifact(path=os.path.join(base,"positioning.md"), kind="md", summary="Positioning one-pager")]
