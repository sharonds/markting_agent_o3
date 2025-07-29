
import os, json, unittest, glob, subprocess, sys

class TestV32ContextAndReports(unittest.TestCase):
    def test_context_and_gate_reports(self):
        subprocess.run([sys.executable, "app/main.py", "--goal", "v3.2 test"], check=True)
        run_dir = sorted(glob.glob("out/*"))[-1]
        art = os.path.join(run_dir, "artifacts")
        self.assertTrue(os.path.exists(os.path.join(art, "context_pack.json")))
        self.assertTrue(os.path.exists(os.path.join(art, "gateA_report.json")))
        cal = json.load(open(os.path.join(art,"calendar.json"),"r",encoding="utf-8"))
        self.assertGreater(len(cal.get("items",[])), 0)
        any_with_cta = any("cta" in i for i in cal["items"])
        self.assertTrue(any_with_cta)
        self.assertTrue(os.path.exists(os.path.join(art, "gateB_report.json")))

if __name__ == "__main__":
    unittest.main()
