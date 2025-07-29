
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

def run(params, ctx):
    return _run_internal(params, ctx)

def _run_internal(params, ctx):
    base = ctx['paths']['artifacts']
    provider = ctx['llm_router'].for_task('strategist')
    schema = load_schema("strategy_pack")
    evidence = read_json(os.path.join(base, "evidence_pack.json"))
    context_pack = ctx.get("context_pack", {})

    if provider.name == "offline":
        obj = _offline_strategy(evidence, context_pack); usage=None
    else:
        role = open("prompts/roles/strategist.md","r",encoding="utf-8").read()
        
        # Create example structure to ensure AI follows the correct schema
        example_structure = {
            "icp": {
                "segments": [{
                    "name": "string",
                    "jobs": ["array of strings"],
                    "pains": ["array of strings"],
                    "gains": ["array of strings"],
                    "triggers": ["array of strings"],
                    "qualifiers": ["array of strings"],
                    "disqualifiers": ["array of strings"],
                    "objections": ["array of strings"]
                }]
            },
            "positioning": {
                "category": "string",
                "for": "string",
                "who": "string", 
                "our_product": "string",
                "is_a": "string",
                "unlike": "string",
                "we": "string",
                "rtbs": [{"text": "string", "evidence_ids": ["array"]}]
            },
            "messaging": {
                "pillars": [
                    {
                        "id": "p1",
                        "name": "string",
                        "claims": ["array of strings"],
                        "evidence_ids": ["array of evidence IDs"],
                        "tones": ["array of strings"],
                        "ctas": ["array of strings"]
                    }
                ]
            }
        }
        
        message = f"""{role}

ContextPack:
{json.dumps(context_pack, indent=2)}

Evidence Pack (JSON):
{json.dumps(evidence, indent=2)[:4000]}

IMPORTANT: Return a JSON object that exactly matches this structure (replace example values with real content):
{json.dumps(example_structure, indent=2)}

Requirements:
- Include ALL required fields shown in the example
- Each messaging pillar MUST have an "id" field (p1, p2, p3, etc.)
- Reference evidence IDs from the evidence pack in evidence_ids arrays
- Use brand name from context_pack for "our_product"

Return ONLY the JSON object. No code fences. No wrapper keys. No additional text.
"""
        messages=[{"role":"system","content":"You are a rigorous strategist producing JSON outputs that exactly match the required schema."},
                  {"role":"user","content": message}]
        try:
            resp = provider.json(messages, schema, temperature=0.3, max_tokens=2500)
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
    
    # Check for required messaging pillar structure and fix missing IDs
    if 'messaging' in obj and 'pillars' in obj['messaging']:
        for i, pillar in enumerate(obj['messaging']['pillars']):
            if 'id' not in pillar:
                print(f"WARNING: Pillar {i} missing 'id' field, adding default")
                pillar['id'] = f"p{i+1}"
    
    try:
        validate_obj("strategy_pack", obj)
    except Exception as ve:
        print(f"ERROR: Strategy pack validation failed: {ve}")
        raise

    write_json(os.path.join(base,"strategy_pack.json"), obj)
    pos_text = f"# Positioning (One-Pager)\n\n**Category**: {obj['positioning'].get('category')}\n\n**Statement**: Unlike {obj['positioning'].get('unlike')}, {obj['positioning'].get('our_product')} helps {context_pack.get('audience','teams')} automate work quickly—connecting 8,000+ apps to turn repetitive tasks into reliable workflows (see evidence f_appcount)."
    write_text(os.path.join(base,"positioning.md"), pos_text + "\n")
    return [Artifact(path=os.path.join(base,"strategy_pack.json"), kind="json", summary="Strategy pack"),
            Artifact(path=os.path.join(base,"positioning.md"), kind="md", summary="Positioning one-pager")]
