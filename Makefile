override SERVICE=media

# Build images for different contexts

build-prod:
	docker build ./ $(ARGS) --tag "openslides-$(SERVICE)" --build-arg CONTEXT="prod" --target "prod"

build-dev:
	docker build ./ $(ARGS) --tag "openslides-$(SERVICE)-dev" --build-arg CONTEXT="dev" --target "dev"

build-tests:
	docker build ./ $(ARGS) --tag "openslides-$(SERVICE)-tests" --build-arg CONTEXT="tests" --target "tests"

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
	@echo "\033[1;33m DEPRECATION WARNING: This make command is deprecated and will be removed soon! \033[0m"

deprecation-warning-alternative: | deprecation-warning
	@echo "\033[1;33m Please use the following command instead: $(ALTERNATIVE) \033[0m"

run-dev run-dev-attach run-dev-attached run-dev-standalone run-dev-interactive stop-dev:
	@make deprecation-warning-alternative ALTERNATIVE="dev and derivative maketargets are now only available in main repository. (use 'make dev-help' in main repository for more information)"

build-dummy-autoupdate: | deprecation-warning
	docker build . -f tests/dummy_autoupdate/Dockerfile.dummy_autoupdate --tag openslides-media-dummy-autoupdate

check-black:
	@make deprecation-warning-alternative ALTERNATIVE="run-lint"
	docker compose -f docker-compose.test.yml exec -T tests black --check --diff src/ tests/

check-isort:
	@make deprecation-warning-alternative ALTERNATIVE="run-lint"
	docker compose -f docker-compose.test.yml exec -T tests isort --check-only --diff src/ tests/

flake8:
	@make deprecation-warning-alternative ALTERNATIVE="run-lint"
	docker compose -f docker-compose.test.yml exec -T tests flake8 src/ tests/

stop-tests:
	docker compose -f docker-compose.test.yml down

start-test-setup: | deprecation-warning build-dev build-tests build-dummy-autoupdate
	docker compose -f docker-compose.test.yml up -d
	docker compose -f docker-compose.test.yml exec -T tests wait-for-it "media:9006"

run-bash:
	@make deprecation-warning-alternative ALTERNATIVE="dev"
	make start-test-setup
	docker compose -f docker-compose.test.yml exec tests bash
