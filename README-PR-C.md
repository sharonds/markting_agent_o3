# PR-C: Unified QA report — generated 2025-07-30T00:28:48.874227Z


**What this adds**
- A single `artifacts/qa_report.json` that summarizes quality checks across the whole pipeline:
  - Evidence coverage (no missing evidence IDs)
  - Provenance (per-pillar average above threshold)
  - Pillar coverage in calendar
  - CTA whitelist adherence (if ContextPack.ctas provided)
  - Post traceability: "Sources:" present and numeric claims cited
  - Locale warnings (non-fatal) for en-GB vs en-US spellings

**Output example**
```json
{
  "score": 0.833,
  "checks": {
    "evidence_coverage_ok": true,
    "provenance_threshold_ok": true,
    "pillar_coverage_ok": true,
    "cta_whitelist_ok": true,
    "post_has_sources": true,
    "numeric_claims_cited": true
  },
  "failures": [],
  "details": { "missing_total": 0, "low_quality": [], "missing_pillars": [], "bad_ctas": [], "locale_warnings": [] }
}
```

**Config**
- Uses `PROVENANCE_MIN_AVG` for provenance threshold (same as PR-B).
- Uses `POST_FILENAME` to locate the copywriter artifact (defaults to `post_linkedin.md`).

**Apply**
```bash
git checkout -b chore/pr-c-qa
unzip -o pr-c-qa-bundle.zip -d .
git add -A
git commit -m "PR-C: unified QA report after Gate B"
git push -u origin chore/pr-c-qa
# open PR to main
```
