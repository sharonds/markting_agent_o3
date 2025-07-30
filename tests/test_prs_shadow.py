
import os, glob, json, unittest, subprocess, sys

class TestPRSShadow(unittest.TestCase):
    def test_tool_usage_written_in_shadow(self):
        env = os.environ.copy()
        env["AUTO_APPROVE"] = "1"
        env["SHADOW"] = "1"
        env["PROVIDER_SEARCH"] = "none"
        env["PROVIDER_KEYWORDS"] = "llm"
        subprocess.run([sys.executable, "app/main.py", "--goal", "PR-S test"], check=True, env=env)
        run_dir = sorted(glob.glob("out/*"))[-1]
        art = os.path.join(run_dir, "artifacts")
        self.assertTrue(os.path.exists(os.path.join(art, "tool_usage.json")))

if __name__ == "__main__":
    unittest.main()
