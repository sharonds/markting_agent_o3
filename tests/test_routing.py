
import os, glob, json, unittest, subprocess, sys

class TestRouting(unittest.TestCase):
    def test_routing_resolved_written(self):
        """Test that routing_resolved.json is generated with correct structure"""
        subprocess.run([sys.executable, "app/main.py", "--goal", "PR-D routing test"], check=True)
        run_dir = sorted(glob.glob("out/*"))[-1]
        art = os.path.join(run_dir, "artifacts")
        path = os.path.join(art, "routing_resolved.json")
        self.assertTrue(os.path.exists(path))
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Test all expected roles are present
        expected_roles = ["researcher", "strategist", "content_planner", "copywriter"]
        for role in expected_roles:
            self.assertIn(role, data, f"Routing should include {role}")
            
        # Test structure of each role config
        for role, config in data.items():
            self.assertIn("provider", config, f"{role} should have provider")
            self.assertIn("temp", config, f"{role} should have temperature")
            self.assertIn(config["provider"], ["openai", "anthropic"], 
                         f"{role} provider should be openai or anthropic")
            self.assertIsInstance(config["temp"], (int, float),
                                f"{role} temperature should be numeric")

    def test_routing_assignments(self):
        """Test that specific roles get expected providers"""
        subprocess.run([sys.executable, "app/main.py", "--goal", "routing assignment test"], check=True)
        run_dir = sorted(glob.glob("out/*"))[-1]
        art = os.path.join(run_dir, "artifacts")
        path = os.path.join(art, "routing_resolved.json")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Test expected provider assignments based on routing config
        expected_assignments = {
            "researcher": "openai",
            "strategist": "anthropic",
            "content_planner": "openai", 
            "copywriter": "openai"
        }
        
        for role, expected_provider in expected_assignments.items():
            self.assertEqual(data[role]["provider"], expected_provider,
                           f"{role} should use {expected_provider}")

if __name__ == "__main__":
    unittest.main()
