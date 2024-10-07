PORT=8000
APP=glowdb

.PHONY: build
build:
	docker compose up -d --build

.PHONY: run
run:
	docker run -p $(PORT):$(PORT) $(APP)

.PHONY: install
install:
	pip install poetry
	poetry install
	poetry shell
	poetry export --without-hashes --format=requirements.txt > requirements.txt

.PHONY: clean
clean:
	rm -rf .venv
	rm -rf ./**/*/__pycache__/
	rm -rf ./**/*.pyc
	rm -rf ./**/*.lock
	rm -rf ./dist
	rm -rf ./build
	rm -rf ./$(APP).egg-info
	rm -rf ./**/__pycache__/
	rm -rf ./.pytest_cache
	rm -rf ./.mypy_cache
	

.PHONY: dev
dev:
	poetry run black .
	poetry run isort .
	poetry run glowdb
	
.PHONY: lint
lint:
	poetry run black .
	poetry run isort .

.PHONY: test
test:
	poetry run pytest




