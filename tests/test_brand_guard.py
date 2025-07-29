import unittest
from app.brand_guard import check_text
class TestBrandGuard(unittest.TestCase):
    def test_detects_banned(self):
        ok, hits = check_text("This is the best in the world", ["best in the world"])
        self.assertFalse(ok); self.assertIn("best in the world", hits)
    def test_allows_clean(self):
        ok, hits = check_text("We are careful and clear", ["best in the world"])
        self.assertTrue(ok); self.assertEqual(hits, [])
if __name__ == "__main__": unittest.main()
