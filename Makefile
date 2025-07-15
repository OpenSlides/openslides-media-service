override SERVICE=media
override MAKEFILE_PATH=../dev/scripts/makefile
override DOCKER_COMPOSE_FILE=docker-compose.test.yml

# Build images for different contexts

build-prod:
	docker build ./ --tag "openslides-$(SERVICE)" --build-arg CONTEXT="prod" --target "prod"

build-dev:
	docker build ./ --tag "openslides-$(SERVICE)-dev" --build-arg CONTEXT="dev" --target "dev"

build-tests:
	docker build ./ --tag "openslides-$(SERVICE)-tests" --build-arg CONTEXT="tests" --target "tests"

# Development

dev dev-help dev-standalone dev-detached dev-stop dev-exec dev-enter:
	bash $(MAKEFILE_PATH)/make-dev.sh "$@" "$(SERVICE)" "$(DOCKER_COMPOSE_FILE)" "$(ARGS)" "bash"

dev-attached:
	make dev-detached
	make dev-exec ARGS='-T tests wait-for-it "media:9006"'
	make dev-enter ARGS='tests'
	make dev-stop

# Tests

run-tests:
	bash dev/run-tests.sh

lint:
	bash dev/run-lint.sh -l

run-tests-ci: | start-test-setup
	docker compose -f docker-compose.test.yml exec -T tests pytest

# Cleanup

run-cleanup: | build-dev
	docker run -ti --entrypoint="" -v `pwd`/src:/app/src -v `pwd`/tests:/app/tests openslides-media-dev bash -c "./execute-cleanup.sh"


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
	bash $(MAKEFILE_PATH)/make-deprecation-warning.sh "dev"
	make dev