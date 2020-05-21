.PHONY: all requirements requirements-prod requirements-dev clean

JQ = jq
JQ_FLAGS = -r
PIPFILE_LOCK = Pipfile.lock
PIPFILE_PROD_SECTION = .default
PIPFILE_DEV_SECTION = .develop
JSON_TRANSFORM_PROD = '.default | to_entries[] | .key + .value.version'
JSON_TRANSFORM_DEV = '.develop | to_entries[] | .key + .value.version'
HOST_IP := $(shell hostname -I | awk '{ print $$1 }')

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

lint:
	@echo "Linting code..."
	flake8 --exclude=migrations

clean:
	@echo "Cleaning up generated files..."
	rm -rvf \
		.pytest_cache \
		htmlcov \
		test-results \
		geckodriver.log \
		builds \
		cache

docker-build:
	sudo docker build --tag vw-type2-id:0.1 .

docker-run:
	# The host-ip needs to resolve to the host's eth0 IP
	sudo docker run \
		--env-file .env \
		--publish 8000:8000 \
		--add-host=database:$(HOST_IP) \
		--volume=static:/opt/vw_type2_id/static \
		vw-type2-id:0.1
