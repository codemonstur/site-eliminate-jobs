
.DEFAULT_GOAL := help
help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

build: ## Render the arguments to wwwroot with pandoc
	@rm -rf wwwroot
	@mkdir -p wwwroot/arguments
	@-cp -r static/* wwwroot/ 2> /dev/null || true
	@for f in arguments/*.md; do \
		[ -e "$$f" ] || continue; \
		pandoc "$$f" -o "wwwroot/arguments/$$(basename "$${f%.md}.html")" --template=templates/argument.html || exit 1; \
	done
	@-cp -r arguments/*.html wwwroot/arguments/ 2> /dev/null || true
