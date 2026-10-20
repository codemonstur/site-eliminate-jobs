
.DEFAULT_GOAL := help
help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

build: ## Render the arguments to docs with pandoc
	@rm -rf docs
	@mkdir -p docs/arguments
	@-cp -r src/static/* docs/ 2> /dev/null || true
	@for f in src/arguments/*.md; do \
		[ -e "$$f" ] || continue; \
		pandoc "$$f" -o "docs/arguments/$$(basename "$${f%.md}.html")" --template=src/templates/argument.html || exit 1; \
	done
	@-cp -r src/arguments/*.html docs/arguments/ 2> /dev/null || true
