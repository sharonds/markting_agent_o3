import os, json, unittest
from jsonschema import Draft2020Validator

def load_json(p): 
    with open(p,"r",encoding="utf-8") as f: return json.load(f)
def load_schema(name):
    with open(os.path.join("schemas", name+".json"),"r",encoding="utf-8") as f: return json.load(f)

class TestContracts(unittest.TestCase):
    def test_schemas_and_traceability(self):
        # Run a flow first (smoke run)
        import subprocess, sys, time
        subprocess.run([sys.executable, "app/main.py", "--goal", "Test run"], check=True)
        # pick newest run
        run_dir = sorted([os.path.join("out",d) for d in os.listdir("out")])[-1]
        art = os.path.join(run_dir,"artifacts")
        # Validate evidence
        evidence = load_json(os.path.join(art,"evidence_pack.json"))
        v = Draft2020Validator(load_schema("evidence_pack")); list(v.iter_errors(evidence))
        self.assertIn("facts", evidence)
        # Strategy
        strat = load_json(os.path.join(art,"strategy_pack.json"))
        v2 = Draft2020Validator(load_schema("strategy_pack")); list(v2.iter_errors(strat))
        self.assertGreaterEqual(len(strat["messaging"]["pillars"]), 1)
        # Calendar
        cal = load_json(os.path.join(art,"calendar.json"))
        v3 = Draft2020Validator(load_schema("calendar")); list(v3.iter_errors(cal))
        self.assertGreaterEqual(len(cal["items"]), 7)
        # pillar ids resolve
        pillar_ids = {p["id"] for p in strat["messaging"]["pillars"]}
        for i in cal["items"]:
            self.assertIn(i["pillar_id"], pillar_ids)
        # copy cites sources
        post = open(os.path.join(art,"post_linkedin.md"),"r",encoding="utf-8").read()
        self.assertIn("Sources:", post)

if __name__ == "__main__":
    unittest.main()
