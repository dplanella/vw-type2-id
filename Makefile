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
