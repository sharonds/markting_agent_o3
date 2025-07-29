import os, json
from datetime import datetime, timedelta
from app.tools.exporters import write_json, write_csv
from app.state import Artifact
from app.validation import validate_obj, load_schema
from app.io import read_json

def _offline_calendar(messaging):
    # 7 days starting from 2025-08-05
    items=[]
    start = datetime(2025,8,5)
    pillar_ids = [p["id"] for p in messaging.get("pillars",[])] or ["p1"]
    intents = ["awareness","consideration","transactional"]
    for i in range(7):
        d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        items.append({"date": d, "channel":"LinkedIn","title": f"Launch teaser #{i+1}","pillar_id": pillar_ids[i % len(pillar_ids)], "intent": intents[i % 3], "status":"draft"})
    return {"items": items}

def run(inputs, ctx) -> list[Artifact]:
    base = ctx['paths']['artifacts']
    strat = read_json(os.path.join(base, "strategy_pack.json"))
    calendar = _offline_calendar(strat.get("messaging",{}))
    errs = validate_obj("calendar", calendar)
    write_json(os.path.join(base,"calendar.json"), calendar)
    # export CSV
    rows=[["date","channel","title","pillar_id","intent","status"]]+[[i["date"], i["channel"], i["title"], i["pillar_id"], i["intent"], i["status"]] for i in calendar["items"]]
    write_csv(os.path.join(base,"content_calendar.csv"), rows)
    return [Artifact(path=os.path.join(base,"calendar.json"), kind="json", summary="Calendar (7 items)"),
            Artifact(path=os.path.join(base,"content_calendar.csv"), kind="csv", summary="Calendar CSV")]
