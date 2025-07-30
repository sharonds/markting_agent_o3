import os, glob, json, unittest, subprocess, sys

class TestQAReport(unittest.TestCase):
    def test_qa_report_generated(self):
        """Test that qa_report.json is generated after Gate B"""
        subprocess.run([sys.executable, "app/main.py", "--goal", "QA report test"], check=True)
        run_dir = sorted(glob.glob("out/*"))[-1]
        art = os.path.join(run_dir, "artifacts")
        qa_path = os.path.join(art, "qa_report.json")
        
        # Check file exists
        self.assertTrue(os.path.exists(qa_path), "qa_report.json should be generated")
        
        # Check file structure
        with open(qa_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Verify required fields
        self.assertIn("score", data, "QA report should have score field")
        self.assertIn("checks", data, "QA report should have checks field")
        self.assertIn("failures", data, "QA report should have failures field")
        self.assertIn("details", data, "QA report should have details field")
        
        # Verify score is a number between 0 and 1
        self.assertIsInstance(data["score"], (int, float))
        self.assertGreaterEqual(data["score"], 0)
        self.assertLessEqual(data["score"], 1)
        
        # Verify checks structure
        checks = data["checks"]
        expected_checks = [
            "evidence_coverage_ok",
            "provenance_threshold_ok", 
            "pillar_coverage_ok",
            "cta_whitelist_ok",
            "post_has_sources",
            "numeric_claims_cited"
        ]
        for check in expected_checks:
            self.assertIn(check, checks, f"QA checks should include {check}")
            self.assertIsInstance(checks[check], bool, f"{check} should be boolean")

    def test_qa_integration_with_summary(self):
        """Test that QA data appears in SUMMARY.md"""
        subprocess.run([sys.executable, "app/main.py", "--goal", "QA integration test"], check=True)
        run_dir = sorted(glob.glob("out/*"))[-1]
        
        # Read SUMMARY.md
        summary_path = os.path.join(run_dir, "SUMMARY.md")
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = f.read()
        
        # Check QA data is included in Quality section
        self.assertIn("## Quality", summary)
        self.assertIn("qa_score:", summary)
        self.assertIn("qa_failures:", summary)

if __name__ == "__main__":
    unittest.main()
