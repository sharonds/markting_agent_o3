import json, logging, os, time
from datetime import datetime

class EventLogger:
    def __init__(self, run_dir: str):
        self.run_dir = run_dir
        os.makedirs(run_dir, exist_ok=True)
        self.jsonl_path = os.path.join(run_dir, "events.jsonl")
        self.human_log_path = os.path.join(run_dir, "run.log")
        self.prompts_dir = os.path.join(run_dir, "prompts")
        self.responses_dir = os.path.join(run_dir, "responses")
        os.makedirs(self.prompts_dir, exist_ok=True)
        os.makedirs(self.responses_dir, exist_ok=True)
        self._setup_logger()

    def _setup_logger(self):
        self.logger = logging.getLogger("orchestrator")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()
        fh = logging.FileHandler(self.human_log_path, encoding="utf-8")
        ch = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        fh.setFormatter(fmt); ch.setFormatter(fmt)
        self.logger.addHandler(fh); self.logger.addHandler(ch)

    def event(self, kind: str, **payload):
        rec = {"ts": datetime.utcnow().isoformat()+"Z","event": kind, **payload}
        with open(self.jsonl_path,"a",encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False)+"\n")
        display = {k:v for k,v in payload.items() if k not in ("content","prompt","response")}
        self.logger.info("%s :: %s", kind, display)

    def save_prompt(self, task_id: str, content: str) -> str:
        path = os.path.join(self.prompts_dir, f"{task_id}.txt")
        with open(path,"w",encoding="utf-8") as f: f.write(content)
        return path

    def save_response_text(self, task_id: str, content: str) -> str:
        path = os.path.join(self.responses_dir, f"{task_id}.txt")
        with open(path,"w",encoding="utf-8") as f: f.write(content)
        return path

    def save_response_json(self, task_id: str, obj: dict) -> str:
        path = os.path.join(self.responses_dir, f"{task_id}.json")
        with open(path,"w",encoding="utf-8") as f: json.dump(obj, f, indent=2, ensure_ascii=False)
        return path

def start_run(out_root="out"):
    run_id = time.strftime("%Y%m%d-%H%M%S")
    run_dir = os.path.join(out_root, run_id)
    os.makedirs(run_dir, exist_ok=True)
    return run_id, run_dir, EventLogger(run_dir)
