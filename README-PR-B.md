
# PR-B: Source validation & provenance (generated 2025-07-29T23:45:18.517164Z)

**What this adds**
- Enriches `evidence_pack.json` with:
  - `canonical_url`, `host`, `reachable`, `status_code`, `provenance_score` (0..1)
- Dedupe: identical `(claim, host)` facts are collapsed.
- Extends **Gate A** report with average provenance per pillar and `low_quality` flag.

**How it works**
- For each fact, we normalise the URL (remove UTM etc.), extract host, optionally perform a `HEAD` request (3s timeout, follow redirects).
- Score = 0.4*host_trust + 0.4*reachable + 0.2*recency(date).

**Config**
- `PROVENANCE_LINK_CHECK` (default `1`): set to `0` to disable HTTP checks (e.g., CI without internet).
- `PROVENANCE_TIMEOUT_SECS` (default `3`).
- `PROVENANCE_MIN_AVG` (default `0.5`): GateA low-quality threshold.

**Apply**
```bash
git checkout -b chore/pr-b-provenance
unzip -o pr-b-provenance-bundle.zip -d .
git add -A
git commit -m "PR-B: evidence provenance enrichment + GateA provenance report"
git push -u origin chore/pr-b-provenance
# open PR to main
```

**Notes**
- Schemas updated so fields are optional; older runs still validate.
- When `PROVENANCE_LINK_CHECK=0`, we assume reachable for scoring to keep tests deterministic.
