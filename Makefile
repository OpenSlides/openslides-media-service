override SERVICE=media
override MAKEFILE_PATH=../dev/scripts/makefile
override DOCKER_COMPOSE_FILE=docker-compose.test.yml

# Build images for different contexts

build-prod:
	docker build ./ --tag "openslides-$(SERVICE)" --build-arg CONTEXT="prod" --target "prod"

build-dev:
	docker build ./ --tag "openslides-$(SERVICE)-dev" --build-arg CONTEXT="dev" --target "dev"

build-test:
	docker build ./ --tag "openslides-$(SERVICE)-tests" --build-arg CONTEXT="tests" --target "tests"

# Development

.PHONY: run-dev%

run-dev%:
	bash $(MAKEFILE_PATH)/make-run-dev.sh "$@" "$(SERVICE)" "$(DOCKER_COMPOSE_FILE)" "$(ARGS)" "bash"

run-dev-attached:
	make run-dev-detached
	make run-dev-exec ARGS='-T tests wait-for-it "media:9006"'
	make run-dev-enter ARGS='tests'
	make run-dev-stop

# Tests

run-tests:
	bash dev/run-tests.sh

run-lint:
	bash dev/run-lint.sh -l

# Cleanup

run-cleanup: | build-dev
	docker run -ti --entrypoint="" -v `pwd`/src:/app/src -v `pwd`/tests:/app/tests openslides-media-dev bash -c "./execute-cleanup.sh"

## TODO
start-test-setup: | build-dev build-test build-dummy-autoupdate
	docker compose -f docker-compose.test.yml up -d
	docker compose -f docker-compose.test.yml exec -T tests wait-for-it "media:9006"

run-tests-ci: | start-test-setup
	docker compose -f docker-compose.test.yml exec -T tests pytest

########################## Deprecation List ##########################

deprecation-warning:
	bash $(MAKEFILE_PATH)/make-deprecation-warning.sh


build-dummy-autoupdate: | deprecation-warning
	docker build . -f tests/dummy_autoupdate/Dockerfile.dummy_autoupdate --tag openslides-media-dummy-autoupdate

check-black:
	bash $(MAKEFILE_PATH)/make-deprecation-warning.sh "run-lint"
	docker compose -f docker-compose.test.yml exec -T tests black --check --diff src/ tests/

check-isort:
	bash $(MAKEFILE_PATH)/make-deprecation-warning.sh "run-lint"
	docker compose -f docker-compose.test.yml exec -T tests isort --check-only --diff src/ tests/

flake8:
	bash $(MAKEFILE_PATH)/make-deprecation-warning.sh "run-lint"
	docker compose -f docker-compose.test.yml exec -T tests flake8 src/ tests/

start-test-setup: | deprecation-warning build-dev build-tests build-dummy-autoupdate
	docker compose -f docker-compose.test.yml up -d
	docker compose -f docker-compose.test.yml exec -T tests wait-for-it "media:9006"

run-bash:
	bash $(MAKEFILE_PATH)/make-deprecation-warning.sh "run-dev"
	make run-dev