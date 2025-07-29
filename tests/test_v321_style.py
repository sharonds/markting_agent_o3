
import os, json, unittest, glob, subprocess, sys

class TestV321Style(unittest.TestCase):
    def test_style_report_exists(self):
        subprocess.run([sys.executable, "app/main.py", "--goal", "v3.2.1 test"], check=True)
        run_dir = sorted(glob.glob("out/*"))[-1]
        art = os.path.join(run_dir, "artifacts")
        self.assertTrue(os.path.exists(os.path.join(art, "style_report.json")))

if __name__ == "__main__":
    unittest.main()
