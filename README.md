# v3.1 PR bundle (generated 2025-07-29T21:19:23.601516Z)

This bundle includes:
- Robust JSON extraction (code fences + wrapper key unwrapping)
- One-shot "repair to schema" retry for JSON outputs
- Strategist/Researcher prompts updated to require **single top-level JSON** (no fences/wrappers)
- Content planner post-processing (pillar_id name→id remap; intent coercion)
- Copywriter: enforce brand name from Compass, always append "Sources: fX, fY"
- Validation shim for jsonschema (Draft2020 vs Draft202012)
- SUMMARY.md health metrics footer

## Apply
1) Create a branch:
   ```bash
   git checkout -b chore/v3.1
   ```
2) Copy the files from this bundle into your repo root (preserving paths).
3) Commit and push:
   ```bash
   git add -A
   git commit -m "v3.1: robust JSON, schema repair, planner remap, summary metrics"
   git push -u origin chore/v3.1
   ```
4) Open a Pull Request to `main`.

## Optional
- Add `export PYTHONPATH=.` to your GitHub Action run step.
- Use `tools/repair_run.py` to normalize older runs if needed.
