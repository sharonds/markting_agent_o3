
import os, unittest
from app.quality.provenance import enhance_evidence

class TestProvenance(unittest.TestCase):
    def test_enhance_no_network(self):
        os.environ["PROVENANCE_LINK_CHECK"]="0"
        evidence = {
            "facts":[
                {"id":"f1","claim":"Zapier connects 8000+ apps","source":"https://zapier.com/apps"},
                {"id":"f2","claim":"Zapier connects 8000+ apps","source":"https://zapier.com/apps?utm_source=foo"},
                {"id":"f3","claim":"Docs","source":"https://developers.google.com"}
            ],
            "competitors": [], "keywords": [], "risks":[]
        }
        out = enhance_evidence(evidence, link_check=True)
        self.assertTrue(len(out["facts"])>=2)
        for f in out["facts"]:
            self.assertIn("host", f)
            self.assertIn("canonical_url", f)
            self.assertIn("provenance_score", f)
        # dedupe (f1, f2) by (claim, host)
        hosts = {f["host"] for f in out["facts"]}
        self.assertIn("zapier.com", hosts)

if __name__ == "__main__":
    unittest.main()
