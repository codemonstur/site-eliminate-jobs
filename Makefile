.DEFAULT_GOAL := help
.PHONY: help build

help: ## Show this help
	@grep -hE '^[a-zA-Z0-9_.-]+:' $(MAKEFILE_LIST) | grep -vE '^[a-zA-Z0-9_.-]+:=' | \
		awk 'BEGIN {FS = ":"} /^\./ {next} {name = $$1; sub(/[[:blank:]]+$$/, "", name); doc = $$0; sub(/^[^#]*## /, "", doc); if (doc == $$0) sub(/^[^:]*:[[:blank:]]*/, "", doc); printf "  \033[36m%-10s\033[0m %s\n", name, doc}'

build: ## Render the arguments to docs with pandoc
	@rm -rf docs
	@mkdir -p docs/arguments
	@-cp -r src/static/* docs/ 2> /dev/null || true
	@for f in src/arguments/*.md; do \
		[ -e "$$f" ] || continue; \
		pandoc "$$f" -o "docs/arguments/$$(basename "$${f%.md}.html")" --template=src/templates/argument.html || exit 1; \
	done
	@-cp -r src/arguments/*.html docs/arguments/ 2> /dev/null || true
