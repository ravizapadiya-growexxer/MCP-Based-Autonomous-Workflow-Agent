.PHONY: install setup run morning evening reset-state list-transitions mcp-server

install:
	pip install -r requirements.txt
	playwright install chromium

setup:
	mkdir -p logs/morning logs/evening logs/error logs/screenshots data
	cp .env.example .env
	@echo "\n✅ Done. Edit .env then run: make run"

run:
	python src/main.py

morning:
	python -c "import asyncio; from src.agents.morning import run_morning; asyncio.run(run_morning())"

evening:
	python -c "import asyncio; from src.agents.evening import run_evening; asyncio.run(run_evening())"

reset-state:
	python scripts/reset_state.py

list-transitions:
	@read -p "Enter any Jira issue key (e.g. DEV-1): " key; \
	python scripts/list_transitions.py $$key

mcp-server:
	python mcp_server/server.py

dry-morning:
	DRY_RUN=true python -c "import asyncio; from src.agents.morning import run_morning; asyncio.run(run_morning())"

dry-evening:
	DRY_RUN=true python -c "import asyncio; from src.agents.evening import run_evening; asyncio.run(run_evening())"
