.PHONY: lint clean

LINTER = flake8
LINTER_ARGS = --exclude=migrations
HOST_IP := $(shell hostname -I | awk '{ print $$1 }')
DOCKER_BIN = docker
DOCKER = sudo $(DOCKER_BIN)
IMAGE_NAME = registry.gitlab.com/vw-type2/vw-type2-id
IMAGE_TAG = master
HOST_CODE_PATH = .
HOST_STATIC_PATH = $(HOST_CODE_PATH)/static
CONT_STATIC_PATH = /opt/vw_type2_id/static


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

docker-build:
	$(DOCKER) build --tag $(IMAGE) .

docker-run:
	# The host-ip needs to resolve to the host's eth0 IP
	$(DOCKER) run \
		--env-file $(HOST_CODE_PATH)/.env \
		--publish 8001:8000 \
		--add-host=database:$(HOST_IP) \
		--volume=$(HOST_STATIC_PATH):$(CONT_STATIC_PATH) \
		$(IMAGE)
