import os, time, json
from app.state import ProjectState, Task, Artifact
from app.logs import EventLogger
from app.agents import researcher, strategist, content_planner, copywriter
from app.db import connect, start_run as db_start_run, end_run as db_end_run, add_task, complete_task, add_artifact, add_gate, resolve_gate
from app.llm_providers import LLMRouter

AGENTS = {
    "researcher": researcher.run,
    "strategist": strategist.run,
    "content_planner": content_planner.run,
    "copywriter": copywriter.run
}

PIPELINE = [
    ("researcher", "Compile research/evidence pack"),
    ("strategist", "Draft ICP + positioning + messaging"),
    ("content_planner", "Build 7–10 item content calendar"),
    ("copywriter", "Draft first LinkedIn post"),
]

def run_pipeline(state: ProjectState, run_dir: str, log: EventLogger) -> ProjectState:
    artifacts_dir = os.path.join(run_dir, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    # DB
    db = connect(os.path.join(run_dir, "run.sqlite"))
    manifest = {
        "models": {},
        "temps": {"researcher":0.2,"strategist":0.3,"content_planner":0.2,"copywriter":0.7},
        "budget_eur": float(os.getenv("BUDGET_EUR", "0"))
    }
    db_start_run(db, os.path.basename(run_dir), state.intake.get("objective",""), manifest.get("budget_eur", 0), model_info=manifest)

    # Router
    router = LLMRouter()
    # Create prompt/response folders in ctx
    ctx = {
        "compass_meta": state.compass_meta,
        "compass_body": state.compass_body,
        "intake": state.intake,
        "paths": {"run": run_dir, "artifacts": artifacts_dir, "prompts": os.path.join(run_dir,"prompts"), "responses": os.path.join(run_dir,"responses")},
        "llm_router": router,
        "db": db,
        "run_id": os.path.basename(run_dir),
        "current_task_id": None
    }

    for role, goal in PIPELINE:
        task = Task(id=f"{int(time.time())}-{role}", role=role, goal=goal)
        state.tasks.append(task)
        log.event("task_started", role=role, goal=goal, task_id=task.id)
        add_task(db, os.path.basename(run_dir), task.id, role, goal)
        ctx["current_task_id"] = task.id
        try:
            arts = AGENTS[role]({}, ctx)
            for a in arts:
                state.artifacts.append(a)
                task.artifacts.append(a)
                add_artifact(db, os.path.basename(run_dir), task.id, a.path, a.kind, a.summary)
            task.status = "done"
            complete_task(db, task.id, "done")
            log.event("task_completed", role=role, task_id=task.id, artifacts=[a.path for a in arts])

            if role == "strategist":
                gate_summary = "Review ICP + Positioning + Messaging (Gate A)"
                add_gate(db, os.path.basename(run_dir), task.id, "GATE_A_POSITIONING", gate_summary)
                with open(os.path.join(run_dir, "pending_gate.json"), "w", encoding="utf-8") as f:
                    json.dump({"gate":"GATE_A_POSITIONING","summary":gate_summary,"task_id":task.id}, f, indent=2)
                log.event("gate_waiting", gate="GATE_A_POSITIONING")
                if os.getenv("AUTO_APPROVE","0") != "1":
                    input(">> Gate A waiting. Press Enter to approve...")
                resolve_gate(db, os.path.basename(run_dir), task.id, "GATE_A_POSITIONING", "approved")
                log.event("gate_resumed", gate="GATE_A_POSITIONING")

            if role == "copywriter":
                gate_summary = "Review First Asset (Gate B)"
                add_gate(db, os.path.basename(run_dir), task.id, "GATE_B_FIRST_ASSET", gate_summary)
                with open(os.path.join(run_dir, "pending_gate.json"), "w", encoding="utf-8") as f:
                    json.dump({"gate":"GATE_B_FIRST_ASSET","summary":gate_summary,"task_id":task.id}, f, indent=2)
                log.event("gate_waiting", gate="GATE_B_FIRST_ASSET")
                if os.getenv("AUTO_APPROVE","0") != "1":
                    input(">> Gate B waiting. Press Enter to approve...")
                resolve_gate(db, os.path.basename(run_dir), task.id, "GATE_B_FIRST_ASSET", "approved")
                log.event("gate_resumed", gate="GATE_B_FIRST_ASSET")

        except Exception as e:
            task.status = "failed"
            complete_task(db, task.id, "failed")
            log.event("task_failed", role=role, task_id=task.id, error=str(e))
            break
        finally:
            ctx["current_task_id"] = None

    # Write summary + manifest
    index_path = os.path.join(run_dir, "SUMMARY.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Run Summary\n\n")
        for t in state.tasks:
            f.write(f"- {t.role}: {t.status}\n")
            for a in t.artifacts:
                f.write(f"  - {a.kind}: {a.path} — {a.summary}\n")
    with open(os.path.join(run_dir, "run_manifest.json"),"w",encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    log.event("run_completed", total_artifacts=len(state.artifacts), index=index_path)
    db_end_run(db, os.path.basename(run_dir), "completed")
    return state
