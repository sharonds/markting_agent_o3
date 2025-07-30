
import os, glob, json, unittest, subprocess, sys

class TestRouting(unittest.TestCase):
    def test_routing_resolved_written(self):
        subprocess.run([sys.executable, "app/main.py", "--goal", "PR-D routing test"], check=True)
        run_dir = sorted(glob.glob("out/*"))[-1]
        art = os.path.join(run_dir, "artifacts")
        path = os.path.join(art, "routing_resolved.json")
        self.assertTrue(os.path.exists(path))
        data = json.load(open(path, "r", encoding="utf-8"))
        self.assertIn("researcher", data)
        self.assertIn("strategist", data)

if __name__ == "__main__":
    unittest.main()
