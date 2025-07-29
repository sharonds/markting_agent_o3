import os, yaml, re, json

def read_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def parse_frontmatter_markdown(path: str):
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", txt, re.S)
    meta = {}
    body = txt
    if m:
        meta = yaml.safe_load(m.group(1)) or {}
        body = m.group(2)
    return meta, body

def read_json(path:str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path:str, obj: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path,"w",encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
