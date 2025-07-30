
import os, glob, json, unittest, subprocess, sys, re

class TestV322Summary(unittest.TestCase):
    def test_quality_section_present(self):
        """Test that Quality section is present in SUMMARY.md"""
        subprocess.run([sys.executable, "app/main.py", "--goal", "v3.2.2 test"], check=True)
        run_dir = sorted(glob.glob("out/*"))[-1]
        summary_path = os.path.join(run_dir, "SUMMARY.md")
        
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = f.read()
        
        self.assertIn("## Quality", summary, "SUMMARY.md should have Quality section")

    def test_budget_banner_present(self):
        """Test that budget information is displayed in Cost section"""
        # Set environment variable for test
        os.environ["BUDGET_EUR"] = "8"
        
        subprocess.run([sys.executable, "app/main.py", "--goal", "v3.2.2 budget test"], check=True)
        run_dir = sorted(glob.glob("out/*"))[-1]
        summary_path = os.path.join(run_dir, "SUMMARY.md")
        
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = f.read()
        
        # Check Cost section exists
        self.assertIn("## Cost", summary, "SUMMARY.md should have Cost section")
        
        # Check budget-related fields
        self.assertIn("budget_eur:", summary, "Should show budget_eur")
        self.assertIn("budget_utilization:", summary, "Should show budget_utilization")
        self.assertIn("8.00", summary, "Should show budget amount")
        self.assertIn("%", summary, "Should show utilization percentage")

    def test_quality_metrics_detailed(self):
        """Test that Quality section contains expected metrics"""
        subprocess.run([sys.executable, "app/main.py", "--goal", "v3.2.2 quality metrics test"], check=True)
        run_dir = sorted(glob.glob("out/*"))[-1]
        summary_path = os.path.join(run_dir, "SUMMARY.md")
        
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = f.read()
        
        # Extract Quality section
        quality_match = re.search(r'## Quality\n(.*?)(?=\n##|\Z)', summary, re.DOTALL)
        self.assertIsNotNone(quality_match, "Should find Quality section")
        
        if quality_match:
            quality_section = quality_match.group(1)
        else:
            self.fail("Quality section not found in SUMMARY.md")
        
        # Check for expected quality metrics
        expected_metrics = [
            "qa_score:",
            "qa_failures:",
            "style_flags:",
            "avg_words_per_sentence:",
            "exclamations:",
            "passive_per_sentence:"
        ]
        
        for metric in expected_metrics:
            self.assertIn(metric, quality_section, f"Quality section should include {metric}")

    def test_cost_breakdown_by_role(self):
        """Test that cost breakdown by role is included"""
        subprocess.run([sys.executable, "app/main.py", "--goal", "v3.2.2 cost breakdown test"], check=True)
        run_dir = sorted(glob.glob("out/*"))[-1]
        summary_path = os.path.join(run_dir, "SUMMARY.md")
        
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = f.read()
        
        # Check for role-based cost breakdown
        self.assertIn("by_role:", summary, "Should show cost breakdown by role")
        self.assertIn("total_estimated_eur:", summary, "Should show total estimated cost")

if __name__ == "__main__":
    unittest.main()
