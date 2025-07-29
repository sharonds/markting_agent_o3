<!-- v3.1.2 addendum (generated 2025-07-29T21:44:26.200696Z) -->
## Post filename & one-command PR

**Control the LinkedIn post filename** via env or Makefile:
```bash
export POST_FILENAME=post_001.md   # default is post_linkedin.md
make run GOAL="Launch beta for EU SMB founders"
# outputs: out/<run-id>/artifacts/post_001.md
```

**Open a branch, run, commit /out, and push a PR** (requires `gh` GitHub CLI authenticated):
```bash
make pr GOAL="Launch beta for EU SMB founders" BRANCH="chore/zapier-eu-beta" POST_FILENAME=post_001.md
```
This will:
1. create/switch to `BRANCH`,
2. run the orchestrator with `AUTO_APPROVE=1`,
3. commit `out/` artifacts,
4. push and open a PR (if `gh` is installed).
