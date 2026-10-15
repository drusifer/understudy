# Understudy - Makefile fronting the project's npm scripts.
#
# package.json "scripts" is the source of truth for HOW each task runs; this
# file gives every task the standard name so `bobp make <target>` works the
# same here as in every other project. See docs/SDLC.md.
#
# Adding a task: add the npm script first, then a one-line target here.

.PHONY: help install test lint check secrets hooks clean distclean

NEED_INSTALL = @test -d node_modules || { echo "No node_modules - run 'make install' first"; exit 1; }

help: ## List targets
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

install: ## Install dependencies exactly as locked (the only target that uses the network)
	@if [ -f package-lock.json ]; then npm ci; else npm install; fi

test: ## Run the unit tests (node:test); ARGS="--test-name-pattern=x" to filter
	$(NEED_INSTALL)
	npm test -- $(ARGS)

lint: ## eslint over src/ and tests/
	$(NEED_INSTALL)
	npm run lint

secrets: ## gitleaks: every commit + uncommitted changes to tracked files
	@command -v gitleaks >/dev/null || { echo "gitleaks is not installed - see https://github.com/gitleaks/gitleaks#installing"; exit 1; }
	gitleaks git --no-banner --redact .
	gitleaks git --no-banner --redact --pre-commit .

hooks: ## Install the gitleaks pre-commit hook (.githooks/)
	git config core.hooksPath .githooks

check: test lint secrets ## Full gate: test + lint + secrets

clean: ## Remove build outputs and caches
	rm -rf build coverage .eslintcache

distclean: clean ## Also remove node_modules
	rm -rf node_modules
