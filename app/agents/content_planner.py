
import os, json, math
from datetime import datetime, timedelta
from app.tools.exporters import write_json, write_csv
from app.state import Artifact
from app.io import read_json

INTENT_SEQUENCE = ["awareness","consideration","transactional"]

def daterange(start, end):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)

def slots_from_context(context_pack, pillars):
    tl = context_pack.get("timeline", {})
    start = datetime.fromisoformat(tl.get("start")) if tl.get("start") else datetime(2025,8,5)
    end = datetime.fromisoformat(tl.get("end")) if tl.get("end") else start + timedelta(days=6)
    channels = context_pack.get("channels") or ["LinkedIn"]
    freq = {"LinkedIn": 3, "Blog": 1, "Email": 1}
    weeks = max(1, math.ceil(((end - start).days + 1) / 7.0))
    items = []
    li_dates = [d for d in daterange(start, end) if d.weekday() in (1,3,5)]
    li_dates = li_dates or [d for d in daterange(start, end)]
    for i, p in enumerate(pillars):
        d = li_dates[i % len(li_dates)]
        items.append({"date": d.strftime("%Y-%m-%d"), "channel":"LinkedIn", "title": f"{p['name']}: quick win", "pillar_id": p["id"], "intent": INTENT_SEQUENCE[i % 3], "status":"draft", "format":"post"})
    for ch in channels:
        count = freq.get(ch, 1) * weeks
        existing = sum(1 for it in items if it["channel"] == ch)
        to_add = max(0, count - existing)
        day_list = [d for d in daterange(start, end)]
        for i in range(to_add):
            d = day_list[(i*2) % len(day_list)]
            items.append({"date": d.strftime("%Y-%m-%d"), "channel": ch, "title": f"{ch} post #{i+1}", "pillar_id": pillars[i % len(pillars)]["id"], "intent": INTENT_SEQUENCE[(i+len(items)) % 3], "status":"draft", "format": "article" if ch=="Blog" else ("campaign" if ch=="Email" else "post")})
    return items

def apply_cta(items, context_pack, pillars):
    ctas = context_pack.get("ctas") or []
    default_cta = (pillars[0].get("ctas") or ["Learn more"])[0] if pillars else "Learn more"
    for it in items:
        it["cta"] = ctas[0] if ctas else default_cta
    return items

def run(inputs, ctx) -> list[Artifact]:
    base = ctx['paths']['artifacts']
    strat = read_json(os.path.join(base, "strategy_pack.json"))
    context_pack = ctx.get("context_pack", {})
    pillars = strat.get("messaging",{}).get("pillars",[])
    items = slots_from_context(context_pack, pillars)
    items = apply_cta(items, context_pack, pillars)
    cal = {"items": items}
    path = os.path.join(base,"calendar.json")
    write_json(path, cal)
    rows=[["date","channel","title","pillar_id","intent","status","format","cta"]]+[[i["date"], i["channel"], i["title"], i["pillar_id"], i["intent"], i["status"], i.get("format",""), i.get("cta","")] for i in cal["items"]]
    write_csv(os.path.join(base,"content_calendar.csv"), rows)
    return [Artifact(path=path, kind="json", summary=f"Calendar ({len(cal['items'])} items)"),
            Artifact(path=os.path.join(base,"content_calendar.csv"), kind="csv", summary="Calendar CSV")]
