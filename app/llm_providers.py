import os, hashlib, requests, json, re
from dataclasses import dataclass
from typing import Optional, List, Union

@dataclass
class LLMResponse:
    text: str
    json_obj: Optional[dict]
    usage: dict

class BaseProvider:
    name="base"
    def chat(self, messages: List[dict], **kw)->LLMResponse: raise NotImplementedError
    def json(self, messages: List[dict], schema: dict, **kw)->LLMResponse:
        r = self.chat(messages, **kw)
        obj = safe_extract_json(r.text)
        return LLMResponse(r.text, obj, r.usage)

def safe_extract_json(text: str):
    # First try to extract JSON from markdown code blocks
    json_blocks = re.findall(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    for block in json_blocks:
        try: 
            return json.loads(block.strip())
        except Exception: 
            continue
    
    # Fallback: Find JSON objects in text
    cands = re.findall(r"\{[\s\S]*\}", text)
    for raw in reversed(cands):
        try: 
            parsed = json.loads(raw)
            # If there's a wrapper object, try to extract the inner content
            if isinstance(parsed, dict) and len(parsed) == 1:
                key = list(parsed.keys())[0]
                if key in ['strategy_pack', 'evidence_pack']:
                    return parsed[key]
            return parsed
        except Exception: 
            continue
    return {}

class OfflineProvider(BaseProvider):
    name="offline"
    def chat(self, messages: List[dict], **kw)->LLMResponse:
        prompt = "\n".join(m.get("content","") for m in messages)
        h = hashlib.sha1(prompt.encode()).hexdigest()[:8]
        return LLMResponse(f"[offline:{h}] placeholder; enable a real provider", None, {"prompt_tokens":len(prompt)//4,"completion_tokens":40})

class OpenAIProvider(BaseProvider):
    name="openai"
    def __init__(self): self.model=os.getenv("OPENAI_MODEL","gpt-4o-mini"); self.key=os.getenv("OPENAI_API_KEY")
    def chat(self, messages, **kw):
        import openai
        client = openai.OpenAI(api_key=self.key) if hasattr(openai,"OpenAI") else openai
        resp = client.chat.completions.create(model=self.model, messages=messages, temperature=kw.get("temperature",0.3), max_tokens=kw.get("max_tokens", 900))
        text = resp.choices[0].message.content; usage=getattr(resp,"usage",{}) or {}
        return LLMResponse(text, None, usage)

class AnthropicProvider(BaseProvider):
    name="anthropic"
    def __init__(self): self.model=os.getenv("ANTHROPIC_MODEL","claude-3-5-sonnet-20240620"); self.key=os.getenv("ANTHROPIC_API_KEY")
    def chat(self, messages, **kw):
        import anthropic
        sys = "\n".join([m["content"] for m in messages if m["role"]=="system"]) or "You are helpful."
        user_msgs = [m for m in messages if m["role"]!="system"]
        content = [{"type":"text","text": m["content"]} for m in user_msgs]
        client = anthropic.Anthropic(api_key=self.key)
        resp = client.messages.create(model=self.model, system=sys, messages=[{"role":"user","content":content}], temperature=kw.get("temperature",0.3), max_tokens=kw.get("max_tokens",900))
        text = "".join([b.text for b in resp.content if getattr(b,"type","")== "text"])
        usage = {"prompt_tokens": getattr(resp.usage,"input_tokens",None), "completion_tokens": getattr(resp.usage,"output_tokens",None)}
        return LLMResponse(text, None, usage)

class OllamaProvider(BaseProvider):
    name="ollama"
    def __init__(self): self.model=os.getenv("OLLAMA_MODEL","llama3.1"); self.host=os.getenv("OLLAMA_HOST","http://localhost:11434")
    def chat(self, messages, **kw):
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        r = requests.post(f"{self.host}/api/generate", json={"model": self.model, "prompt": prompt, "stream": False, "temperature": kw.get("temperature",0.3)})
        r.raise_for_status(); data = r.json()
        return LLMResponse(data.get("response",""), None, {"prompt_tokens":None,"completion_tokens":None})

PROVIDERS={"offline":OfflineProvider,"openai":OpenAIProvider,"anthropic":AnthropicProvider,"ollama":OllamaProvider}

class LLMRouter:
    def __init__(self, config: Union[dict, None] = None): self.config=config or {}; self.cache={}
    def _make(self, name:str): return PROVIDERS.get(name, OfflineProvider)()
    def for_task(self, task_role:str):
        env = f"LLM_{task_role.upper()}"
        provider = os.getenv(env) or self.config.get(task_role) or os.getenv("LLM_DEFAULT","offline")
        key=f"prov:{provider}"; 
        if key not in self.cache: self.cache[key]=self._make(provider)
        return self.cache[key]
