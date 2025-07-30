
import os, glob, json, unittest, subprocess, sys

class TestV322Summary(unittest.TestCase):
    def test_quality_section_present(self):
        subprocess.run([sys.executable, "app/main.py", "--goal", "v3.2.2 test"], check=True)
        run_dir = sorted(glob.glob("out/*"))[-1]
        summary = open(os.path.join(run_dir, "SUMMARY.md"), "r", encoding="utf-8").read()
        self.assertIn("## Quality", summary)

if __name__ == "__main__":
    unittest.main()
