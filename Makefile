# Understudy - the project's task front door (Python only: uv, unittest, ruff). See docs/SDLC.md.
#
# Adding a task: add a one-line target here with a `## description`; `bobp make help` lists them.

.PHONY: help install lock install-py lock-py test test-py lint check secrets hooks push run dashboard clean distclean

# Live targets (run) read API keys from .env (gitignored; `export NAME=value` lines);
# test never does, so it can never reach a paid or networked service.
LOAD_ENV = set -a; if [ -f .env ]; then . ./.env; fi; set +a;

help: ## List targets
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-16s %s\n", $$1, $$2}'

install: install-py ## Install dependencies exactly as locked (network on first setup)

lock: lock-py ## Refresh uv.lock from pyproject.toml (network)

install-py: ## Install the pinned Python environment from uv.lock (network on first setup)
	@if [ ! -f uv.lock ]; then uv lock --python 3.12.15; fi
	uv sync --locked

lock-py: ## Refresh uv.lock from pyproject.toml (network)
	uv lock --python 3.12.15

test: test-py ## Run the unit tests; ARGS="test_sketch*.py" runs only the files matching that pattern

test-py: ## Run Python unit tests (ARGS="test_sketch*.py" runs only the files matching that pattern)
	@test -x .venv/bin/python || { echo "No .venv - run 'bobp make install' first"; exit 1; }
	.venv/bin/python -m unittest discover -s tests/python -p '$(if $(ARGS),$(ARGS),test_*.py)'

run: ## Run the understudy command: ARGS="run coffee_week.yaml" | "check coffee_week.yaml" | "dashboard" | "run examples/household/household.yaml --with monarch=... --with amex=... --with amex_account=..."
	@$(LOAD_ENV) bin/understudy $(ARGS)

dashboard: ## Serve the operations console over build/runs on 0.0.0.0:4180 (ARGS="build/runs --port 4180")
	@bin/understudy dashboard $(ARGS)

lint: ## ruff over the Python
	@test -x .venv/bin/ruff || { echo "No .venv - run 'bobp make install' first"; exit 1; }
	.venv/bin/ruff check src tests/python

secrets: ## gitleaks: every commit + uncommitted changes to tracked files
	@command -v gitleaks >/dev/null || { echo "gitleaks is not installed - see https://github.com/gitleaks/gitleaks#installing"; exit 1; }
	gitleaks git --no-banner --redact .
	gitleaks git --no-banner --redact --pre-commit .

hooks: ## Install the gitleaks pre-commit hook (.githooks/)
	git config core.hooksPath .githooks

check: test lint secrets ## Full gate: test + lint + secrets

export MSG
push: check ## Commit everything (MSG="...") and push the current branch + its tags, after the full gate; never forced; ARGS="--dry-run" previews
	@scripts/push.sh $(ARGS)

clean: ## Remove build outputs and caches
	@mkdir -p build
	@find build -mindepth 1 -maxdepth 1 ! -name build.out -exec rm -rf {} +
	rm -rf coverage

distclean: clean ## Also remove the Python environment
	rm -rf .venv
