#!/usr/bin/env bash
set -euo pipefail
GOAL="${1:-Launch beta for EU SMB founders}"
BRANCH="${2:-chore/run-$(date +%Y%m%d-%H%M%S)}"
POST_FILENAME="${3:-post_linkedin.md}"

echo "==> Branch: $BRANCH"
git checkout -b "$BRANCH" || git checkout "$BRANCH"

echo "==> Running orchestrator with AUTO_APPROVE=1"
export PYTHONPATH=.
export AUTO_APPROVE=1
export BUDGET_EUR="${BUDGET_EUR:-8}"
export POST_FILENAME="$POST_FILENAME"
: "${LLM_RESEARCHER:=openai}"; export LLM_RESEARCHER
: "${LLM_STRATEGIST:=anthropic}"; export LLM_STRATEGIST
: "${LLM_CONTENT_PLANNER:=openai}"; export LLM_CONTENT_PLANNER
: "${LLM_COPYWRITER:=openai}"; export LLM_COPYWRITER

python app/main.py --goal "$GOAL"

echo "==> Committing /out artifacts"
git add -A out
if git diff --cached --quiet; then
  echo "No changes in out/ to commit."
else
  git commit -m "Run: $(date -u +%Y-%m-%d) — ${GOAL} [AUTO_APPROVE=1]"
fi
git push -u origin "$BRANCH"

if command -v gh >/dev/null 2>&1; then
  echo "==> Creating PR via gh"
  gh pr create --fill --base main --head "$BRANCH" || true
else
  echo "gh CLI not found. Open a PR from branch '$BRANCH' to 'main'."
fi
