.PHONY: install setup run morning evening test-jira view-state docker-build docker-up docker-down

install:
	pip install -r requirements.txt
	playwright install chromium

setup:
	python scripts/setup.py

run:
	python -m scheduler.main_scheduler

morning:
	python scripts/run_morning.py

evening:
	python scripts/run_evening.py

test-jira:
	python scripts/test_jira.py

view-state:
	python scripts/view_state.py

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down
