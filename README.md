# Marketing Agents (Python) — v3 (generated 2025-07-29T19:36:41.439298Z)

Plan B MVP with:
- 4 agents (Researcher, Strategist, Planner, Copywriter)
- JSON schemas + contract tests
- Multi-provider LLM router (offline/openai/anthropic/ollama)
- Gate A / Gate B with pause
- Prompt/response capture + SQLite run DB
- Budget hooks

Run:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export LLM_DEFAULT=offline
python app/main.py --goal "Launch beta for EU SMB founders"
```
