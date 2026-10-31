# Understudy - Makefile fronting the project's npm scripts.
#
# package.json "scripts" is the source of truth for HOW each task runs; this
# file gives every task the standard name so `bobp make <target>` works the
# same here as in every other project. See docs/SDLC.md.
#
# Adding a task: add the npm script first, then a one-line target here.

.PHONY: help install install-js lock-js install-py lock-py test test-js test-py lint check secrets hooks push run clean distclean

NEED_INSTALL = @test -d node_modules || { echo "No node_modules - run 'bobp make install' first"; exit 1; }

# Live targets (run) read API keys from .env (gitignored; `export NAME=value` lines);
# test never does, so it can never reach a paid or networked service.
LOAD_ENV = set -a; if [ -f .env ]; then . ./.env; fi; set +a;

help: ## List targets
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-16s %s\n", $$1, $$2}'

install: ## Install dependencies exactly as locked (network)
	$(MAKE) install-js
	$(MAKE) install-py

install-js: ## Install Node dependencies exactly as locked (network)
	@if [ -f package-lock.json ]; then npm ci; else npm install; fi

lock-js: ## Refresh the npm lockfile from package.json (network)
	npm install --package-lock-only --ignore-scripts

install-py: ## Install the pinned Python environment from uv.lock (network on first setup)
	@if [ ! -f uv.lock ]; then uv lock --python 3.12.15; fi
	uv sync --locked

lock-py: ## Refresh uv.lock from pyproject.toml (network)
	uv lock --python 3.12.15

test: ## Run the unit tests (node:test); ARGS="--test-name-pattern=x" to filter
	$(MAKE) test-js
	$(MAKE) test-py

test-js: ## Run JavaScript unit tests
	$(NEED_INSTALL)
	npm run test:js -- $(ARGS)

test-py: ## Run Python unit tests (ARGS="test_sketch*.py" runs only the files matching that pattern)
	@test -x .venv/bin/python || { echo "No .venv - run 'bobp make install' first"; exit 1; }
	.venv/bin/python -m unittest discover -s tests/python -p '$(if $(ARGS),$(ARGS),test_*.py)'

run: ## Run the understudy command: ARGS="run coffee_week.yaml" | "check coffee_week.yaml" | "run examples/household/household.yaml --with monarch=... --with amex=... --with amex_account=..."
	$(NEED_INSTALL)
	@test -f bin/understudy.mjs || { echo "bin/understudy.mjs does not exist yet (sprint 1, phase 2)"; exit 1; }
	@$(LOAD_ENV) node bin/understudy.mjs $(ARGS)

lint: ## eslint over src/ and tests/, ruff over the Python
	$(NEED_INSTALL)
	npm run lint
	@test -x .venv/bin/ruff || { echo "No .venv - run 'bobp make install' first"; exit 1; }
	.venv/bin/ruff check src/sketch src/jev.py src/paths.py tests/python

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
	rm -rf coverage .eslintcache

distclean: clean ## Also remove node_modules
	rm -rf node_modules .venv
