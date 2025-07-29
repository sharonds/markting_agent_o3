# Tiny helpers for local dev (generated 2025-07-29T21:41:07.342833Z)
.PHONY: setup run test ci-run repair-run

PY?=python
GOAL?=Launch beta for EU SMB founders
RUN_DIR?=$(shell ls -td out/* 2>/dev/null | head -1)

setup:
	{-e "import sys; assert sys.version_info>=(3,10), 'Python>=3.10 recommended'" || true}
	$(PY) -m pip install --upgrade pip
	@if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
	pip install openai anthropic

run:
	# Uses env from your shell or VS Code envFile
	$(PY) app/main.py --goal "$(GOAL)"

test:
	$(PY) -m unittest -v

ci-run:
	OPENAI_API_KEY=$$OPENAI_API_KEY \
	ANTHROPIC_API_KEY=$$ANTHROPIC_API_KEY \
	LLM_RESEARCHER=openai LLM_STRATEGIST=anthropic LLM_CONTENT_PLANNER=openai LLM_COPYWRITER=openai \
	AUTO_APPROVE=1 BUDGET_EUR=8 \
	PYTHONPATH=. $(PY) app/main.py --goal "$(GOAL)"

repair-run:
	@if [ -z "$(RUN_DIR)" ]; then echo "No run dir found under out/"; exit 1; fi
	$(PY) tools/repair_run.py $(RUN_DIR)
