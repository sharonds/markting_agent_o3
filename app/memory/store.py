
import os, sqlite3, json, time, hashlib
from typing import Dict, Any, List, Tuple

DEFAULT_DB = os.getenv("MEMORY_DB_PATH", "memory.sqlite")

SCHEMA = [
    """create table if not exists facts (
        id text primary key,
        claim text,
        source text,
        host text,
        geo text,
        date text,
        first_seen_ts real,
        last_seen_ts real,
        uses integer default 0
    )""",
    """create table if not exists segments (
        id text primary key,
        name text,
        qualifiers text,
        disqualifiers text,
        objections text,
        first_seen_ts real,
        last_seen_ts real
    )""",
    """create table if not exists pillars (
        id text primary key,
        name text,
        claims text,
        evidence_ids text,
        tones text,
        ctas text,
        first_seen_ts real,
        last_seen_ts real
    )"""
]

def open_db(path: str = None):
    path = path or DEFAULT_DB
    conn = sqlite3.connect(path)
    conn.execute("pragma journal_mode=WAL;")
    conn.execute("pragma synchronous=NORMAL;")
    for stmt in SCHEMA:
        conn.execute(stmt)
    conn.commit()
    return conn

def _now():
    return time.time()

def _gen_fact_id(claim: str, host: str) -> str:
    raw = f"{(claim or '').strip().lower()}|{(host or '').strip().lower()}"
    return "f_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]

def upsert_fact(conn, f: Dict[str, Any]) -> str:
    fid = f.get("id") or _gen_fact_id(f.get("claim",""), f.get("host",""))
    row = conn.execute("select id from facts where id = ?", (fid,)).fetchone()
    if row:
        conn.execute("""update facts set claim=?, source=?, host=?, geo=?, date=?, last_seen_ts=? where id=?""", 
                     (f.get("claim"), f.get("source") or f.get("canonical_url"), f.get("host"), f.get("geo"), f.get("date"), _now(), fid))
    else:
        conn.execute("""insert into facts (id, claim, source, host, geo, date, first_seen_ts, last_seen_ts, uses)
                        values (?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                     (fid, f.get("claim"), f.get("source") or f.get("canonical_url"), f.get("host"), f.get("geo"), f.get("date"), _now(), _now()))
    return fid

def upsert_segment(conn, s: Dict[str, Any]) -> str:
    sid = s.get("id") or "seg_" + hashlib.sha1((s.get("name","")).encode("utf-8")).hexdigest()[:10]
    row = conn.execute("select id from segments where id = ?", (sid,)).fetchone()
    payload = (
        s.get("name"),
        json.dumps(s.get("qualifiers", []), ensure_ascii=False),
        json.dumps(s.get("disqualifiers", []), ensure_ascii=False),
        json.dumps(s.get("objections", []), ensure_ascii=False),
        _now(), sid
    )
    if row:
        conn.execute("""update segments set name=?, qualifiers=?, disqualifiers=?, objections=?, last_seen_ts=? where id=?""", payload)
    else:
        conn.execute("""insert into segments (id, name, qualifiers, disqualifiers, objections, first_seen_ts, last_seen_ts)
                        values (?, ?, ?, ?, ?, ?, ?)""", 
                     (sid, s.get("name"),
                      json.dumps(s.get("qualifiers", []), ensure_ascii=False),
                      json.dumps(s.get("disqualifiers", []), ensure_ascii=False),
                      json.dumps(s.get("objections", []), ensure_ascii=False),
                      _now(), _now()))
    return sid

def upsert_pillar(conn, p: Dict[str, Any]) -> str:
    pid = p.get("id") or "p_" + hashlib.sha1((p.get("name","")).encode("utf-8")).hexdigest()[:10]
    row = conn.execute("select id from pillars where id = ?", (pid,)).fetchone()
    payload = (
        p.get("name"),
        json.dumps(p.get("claims", []), ensure_ascii=False),
        json.dumps(p.get("evidence_ids", []), ensure_ascii=False),
        json.dumps(p.get("tones", []), ensure_ascii=False),
        json.dumps(p.get("ctas", []), ensure_ascii=False),
        _now(), pid
    )
    if row:
        conn.execute("""update pillars set name=?, claims=?, evidence_ids=?, tones=?, ctas=?, last_seen_ts=? where id=?""", payload)
    else:
        conn.execute("""insert into pillars (id, name, claims, evidence_ids, tones, ctas, first_seen_ts, last_seen_ts)
                        values (?, ?, ?, ?, ?, ?, ?, ?)""", 
                     (pid, p.get("name"),
                      json.dumps(p.get("claims", []), ensure_ascii=False),
                      json.dumps(p.get("evidence_ids", []), ensure_ascii=False),
                      json.dumps(p.get("tones", []), ensure_ascii=False),
                      json.dumps(p.get("ctas", []), ensure_ascii=False),
                      _now(), _now()))
    return pid

def load_snapshot(conn, limits: Dict[str,int] = None) -> Dict[str, Any]:
    limits = limits or {"facts": 50, "segments": 10, "pillars": 10}
    cur = conn.cursor()
    facts = [{"id": r[0], "claim": r[1], "source": r[2], "host": r[3], "geo": r[4], "date": r[5]}
             for r in cur.execute("select id, claim, source, host, geo, date from facts order by last_seen_ts desc limit ?", (limits["facts"],))]
    segments = [{"id": r[0], "name": r[1], "qualifiers": json.loads(r[2] or "[]"), "disqualifiers": json.loads(r[3] or "[]"), "objections": json.loads(r[4] or "[]")}
                for r in cur.execute("select id, name, qualifiers, disqualifiers, objections from segments order by last_seen_ts desc limit ?", (limits["segments"],))]
    pillars = [{"id": r[0], "name": r[1], "claims": json.loads(r[2] or "[]"), "evidence_ids": json.loads(r[3] or "[]"), "tones": json.loads(r[4] or "[]"), "ctas": json.loads(r[5] or "[]")}
               for r in cur.execute("select id, name, claims, evidence_ids, tones, ctas from pillars order by last_seen_ts desc limit ?", (limits["pillars"],))]
    return {
        "facts": facts,
        "segments": segments,
        "pillars": pillars,
        "stats": {
            "facts_total": cur.execute("select count(*) from facts").fetchone()[0],
            "segments_total": cur.execute("select count(*) from segments").fetchone()[0],
            "pillars_total": cur.execute("select count(*) from pillars").fetchone()[0]
        }
    }

def persist_from_artifacts(conn, evidence_pack: Dict[str, Any], strategy_pack: Dict[str, Any]) -> Dict[str,int]:
    counts = {"facts":0, "segments":0, "pillars":0}
    for f in evidence_pack.get("facts", []):
        upsert_fact(conn, f); counts["facts"] += 1
    for s in (strategy_pack.get("icp") or {}).get("segments", []):
        upsert_segment(conn, s); counts["segments"] += 1
    for p in (strategy_pack.get("messaging") or {}).get("pillars", []):
        upsert_pillar(conn, p); counts["pillars"] += 1
    conn.commit()
    return counts
