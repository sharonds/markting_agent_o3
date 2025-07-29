import os, unittest
from app.db import connect, start_run, add_task, complete_task, add_artifact
from app.llm_providers import LLMRouter
class TestDBAndRouter(unittest.TestCase):
    def test_db(self):
        os.makedirs("out_test", exist_ok=True)
        db = connect("out_test/router_run.sqlite")
        start_run(db, "run123", "goal", 0, {"models":{}})
        add_task(db, "run123", "t1", "researcher", "do it")
        complete_task(db, "t1", "done")
        open("out_test/a.txt","w").write("x"); add_artifact(db, "run123", "t1", "out_test/a.txt", "txt", "demo")
        cur = db.execute("select count(*) from artifacts"); assert cur.fetchone()[0] > 0
    def test_router(self):
        r = LLMRouter({"strategist":"offline"}); prov = r.for_task("strategist")
        assert getattr(prov, "name", "") == "offline"
if __name__ == "__main__": unittest.main()
