.PHONY: all requirements requirements-prod requirements-dev clean

JQ = jq
JQ_FLAGS = -r
PIPFILE_LOCK = Pipfile.lock
PIPFILE_PROD_SECTION = .default
PIPFILE_DEV_SECTION = .develop
JSON_TRANSFORM_PROD = '.default | to_entries[] | .key + .value.version'
JSON_TRANSFORM_DEV = '.develop | to_entries[] | .key + .value.version'

all: requirements

requirements: requirements-prod requirements-dev

requirements-prod:
	@echo "Generating fake requirements.txt for production..."
	${JQ} ${JQ_FLAGS} ${JSON_TRANSFORM_PROD} \
		${PIPFILE_LOCK} > requirements.txt

requirements-dev:
	@echo "Generating fake requirements-dev.txt for development..."
	${JQ} ${JQ_FLAGS} ${JSON_TRANSFORM_DEV} \
		${PIPFILE_LOCK} > requirements-dev.txt

clean:
	@echo "Cleaning up generated files..."
	rm -rvf \
		.pytest_cache \
		htmlcov \
		test-results \
		geckodriver.log \
		builds \
		cache