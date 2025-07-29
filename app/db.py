import os, sqlite3, json, time, hashlib
from typing import Union

SCHEMA=[
"""CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, goal TEXT, started_at REAL, ended_at REAL, status TEXT, budget_eur REAL DEFAULT 0, spent_eur REAL DEFAULT 0, model_info TEXT);""",
"""CREATE TABLE IF NOT EXISTS tasks (task_id TEXT PRIMARY KEY, run_id TEXT, role TEXT, goal TEXT, status TEXT, started_at REAL, ended_at REAL);""",
"""CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, task_id TEXT, role TEXT, model TEXT, content TEXT, usage_prompt INTEGER, usage_completion INTEGER, created_at REAL);""",
"""CREATE TABLE IF NOT EXISTS artifacts (id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, task_id TEXT, path TEXT, kind TEXT, summary TEXT, sha256 TEXT, created_at REAL);""",
"""CREATE TABLE IF NOT EXISTS gates (id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, task_id TEXT, name TEXT, status TEXT, summary TEXT, created_at REAL, resolved_at REAL);"""
]

def connect(db_path:str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db = sqlite3.connect(db_path); db.execute("PRAGMA journal_mode=WAL;")
    for s in SCHEMA: db.execute(s)
    db.commit()
    return db

def start_run(db, run_id:str, goal:str, budget_eur:float=0, model_info:Union[dict, None]=None):
    db.execute("INSERT OR REPLACE INTO runs(run_id,goal,started_at,status,budget_eur,model_info) VALUES (?,?,?,?,?,?)",
               (run_id, goal, time.time(), "running", budget_eur, json.dumps(model_info or {}))); db.commit()

def end_run(db, run_id:str, status:str="completed"):
    db.execute("UPDATE runs SET ended_at=?, status=? WHERE run_id=?", (time.time(), status, run_id)); db.commit()

def add_task(db, run_id:str, task_id:str, role:str, goal:str):
    db.execute("INSERT INTO tasks(task_id,run_id,role,goal,status,started_at) VALUES (?,?,?,?,?,?)", (task_id, run_id, role, goal, "running", time.time())); db.commit()

def complete_task(db, task_id:str, status:str="done"):
    db.execute("UPDATE tasks SET status=?, ended_at=? WHERE task_id=?", (status, time.time(), task_id)); db.commit()

def add_message(db, run_id, task_id, role, model, content, usage:Union[dict, None]):
    db.execute("INSERT INTO messages(run_id,task_id,role,model,content,usage_prompt,usage_completion,created_at) VALUES (?,?,?,?,?,?,?,?)",
               (run_id, task_id, role, model, content, (usage or {}).get("prompt_tokens"), (usage or {}).get("completion_tokens"), time.time())); db.commit()

def add_artifact(db, run_id, task_id, path, kind, summary):
    try: sha = hashlib.sha256(open(path,"rb").read()).hexdigest()
    except Exception: sha = ""
    db.execute("INSERT INTO artifacts(run_id,task_id,path,kind,summary,sha256,created_at) VALUES (?,?,?,?,?,?,?)",
               (run_id, task_id, path, kind, summary, sha, time.time())); db.commit()

def add_gate(db, run_id, task_id, name, summary):
    db.execute("INSERT INTO gates(run_id,task_id,name,status,summary,created_at) VALUES (?,?,?,?,?,?)",
               (run_id, task_id, name, "waiting", summary, time.time())); db.commit()

def resolve_gate(db, run_id, task_id, name, status):
    db.execute("UPDATE gates SET status=?, resolved_at=? WHERE run_id=? AND task_id=? AND name=?", (status, time.time(), run_id, task_id, name)); db.commit()
