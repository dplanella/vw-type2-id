.PHONY: lint clean

LINTER = flake8
LINTER_ARGS = --exclude=migrations

lint:
	@echo "Linting code..."
	$(LINTER) $(LINTER_ARGS)

clean:
	@echo "Cleaning up generated files..."
	rm -rvf \
		.pytest_cache \
		htmlcov \
		test-results \
		geckodriver.log \
		builds \
		cache

.PHONY: messages

messages:
	@echo "Regenerating translation catalogs..."
	python manage.py makemessages --all --keep-pot --add-location file \
		--ignore=.venv --ignore=static
	@# Undo changes that only touch the creation date
	@for f in $$(git diff --name-only -- vw_type2_id/locale); do \
		git diff --quiet -I POT-Creation-Date -- "$$f" && git checkout -q -- "$$f"; \
	done; true
