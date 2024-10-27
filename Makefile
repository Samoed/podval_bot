.DEFAULT_GOAL := all
DIRS = src/
poetry = poetry run
isort = isort
black = black
mypy = mypy
flake8  = flake8
pyupgrade = pyupgrade --py311-plus


.PHONY: install-linting
install-linting:
	poetry add ruff -G dev

.PHONY: format
format:
	$(poetry) ruff $(DIRS)
#	$(poetry) mypy $(DIRS)

.PHONY: export-dependencies
export-dependencies:
	poetry export -f requirements.txt --output requirements.txt
	poetry export -f requirements.txt --output requirements-dev.txt --with=dev

.PHONY: database
database:
	docker compose up database -d

.PHONY: bot
bot:
	docker compose up bot -d --build

.PHONY: test
test:
	poetry run pytest --cov=app --cov-report=html

.PHONY: migrate
migrate:
	@read -p "Enter migration message: " message; \
	poetry run alembic revision --autogenerate -m "$$message"

.PHONY: downgrade
downgrade:
	poetry run alembic downgrade -1

.PHONY: upgrade
upgrade:
	poetry run alembic upgrade +1

.PHONY: upgrade-offline
upgrade-offline:
	poetry run alembic upgrade head --sql

.PHONY: deploy
deploy:
	docker compose up -d --build

.PHONY: all
all: format export-dependencies
