import json, os
from jsonschema import Draft202012Validator

SCHEMAS = {}
def load_schema(name: str):
    global SCHEMAS
    if name in SCHEMAS: return SCHEMAS[name]
    path = os.path.join("schemas", f"{name}.json")
    with open(path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    SCHEMAS[name] = schema
    return schema

def validate_obj(name: str, obj: dict):
    schema = load_schema(name)
    v = Draft202012Validator(schema)
    errs = sorted(v.iter_errors(obj), key=lambda e: e.path)
    return errs
