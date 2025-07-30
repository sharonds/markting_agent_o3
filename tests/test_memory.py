
import os, glob, json, unittest, subprocess, sys

class TestMemory(unittest.TestCase):
    def test_memory_snapshot_and_persist(self):
        subprocess.run([sys.executable, "app/main.py", "--goal", "PR-A memory test 1"], check=True)
        run1 = sorted(glob.glob("out/*"))[-1]
        art1 = os.path.join(run1, "artifacts")
        self.assertTrue(os.path.exists(os.path.join(art1, "memory_snapshot.json")))
        self.assertTrue(os.path.exists(os.path.join(art1, "memory_persist_report.json")))

        subprocess.run([sys.executable, "app/main.py", "--goal", "PR-A memory test 2"], check=True)
        run2 = sorted(glob.glob("out/*"))[-1]
        art2 = os.path.join(run2, "artifacts")
        self.assertTrue(os.path.exists(os.path.join(art2, "memory_snapshot.json")))
        self.assertTrue(os.path.exists(os.path.join(art2, "memory_persist_report.json")))

if __name__ == "__main__":
    unittest.main()
