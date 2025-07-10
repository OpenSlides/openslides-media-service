SERVICE=media

build-prod:
	docker build ./ --tag "openslides-$(SERVICE)" --build-arg CONTEXT="prod" --target "prod"

build-dev:
	docker build ./ --tag "openslides-$(SERVICE)-dev" --build-arg CONTEXT="dev" --target "dev"

build-test:
	docker build ./ --tag "openslides-$(SERVICE)-tests" --build-arg CONTEXT="tests" --target "tests"

build-dummy-autoupdate:
	docker build . -f tests/dummy_autoupdate/Dockerfile.dummy_autoupdate --tag openslides-media-dummy-autoupdate

run-tests:
	bash dev/run-tests.sh

run-dev run-bash: | start-test-setup
	docker compose -f docker-compose.test.yml exec tests bash

check-black:
	docker compose -f docker-compose.test.yml exec -T tests black --check --diff src/ tests/

check-isort:
	docker compose -f docker-compose.test.yml exec -T tests isort --check-only --diff src/ tests/

flake8:
	docker compose -f docker-compose.test.yml exec -T tests flake8 src/ tests/

stop-tests:
	docker compose -f docker-compose.test.yml down

run-cleanup: | build-dev
	docker run -ti --entrypoint="" -v `pwd`/src:/app/src -v `pwd`/tests:/app/tests openslides-media-dev bash -c "./execute-cleanup.sh"

start-test-setup: | build-dev build-test build-dummy-autoupdate
	docker compose -f docker-compose.test.yml up -d
	docker compose -f docker-compose.test.yml exec -T tests wait-for-it "media:9006"

run-tests-ci: | start-test-setup
	docker compose -f docker-compose.test.yml exec -T tests pytest