
import os, glob, json, unittest, subprocess, sys

class TestExperimentHarness(unittest.TestCase):
    def test_experiment_and_metrics_present(self):
        env = os.environ.copy()
        env["EXPERIMENT_ID"] = "ci_test"
        env["VARIANT"] = "baseline"
        env["SCENARIO"] = "unit"
        env["RUN_NUMBER"] = "1"
        env["AUTO_APPROVE"] = "1"
        subprocess.run([sys.executable, "app/main.py", "--goal", "PR-X test"], check=True, env=env)
        run_dir = sorted(glob.glob("out/*"))[-1]
        art = os.path.join(run_dir, "artifacts")
        self.assertTrue(os.path.exists(os.path.join(art, "experiment.json")))
        self.assertTrue(os.path.exists(os.path.join(art, "metrics.json")))
        m = json.load(open(os.path.join(art, "metrics.json"), "r", encoding="utf-8"))
        self.assertIn("qa", m)
        self.assertIn("evidence", m)

if __name__ == "__main__":
    unittest.main()
