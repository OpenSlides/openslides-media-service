#!/bin/bash

# Executes all tests. Should errors occur, CATCH will be set to 1, causing an erroneous exit code.

echo "########################################################################"
echo "###################### Run Tests and Linters ###########################"
echo "########################################################################"

# Parameters
PERSIST_CONTAINERS=$1

# Setup
CATCH=0

# Builds
if [ "$(docker images -q openslides-media-dev)" = "" ]; then make build-dev || CATCH=1; fi
if [ "$(docker images -q openslides-media-tests)" = "" ]; then make build-test || CATCH=1; fi
docker build . -f tests/dummy_autoupdate/Dockerfile.dummy_autoupdate --tag openslides-media-dummy-autoupdate || CATCH=1

# Execution
docker compose -f docker-compose.test.yml up -d || CATCH=1
docker compose -f docker-compose.test.yml exec -T tests wait-for-it "media:9006" || CATCH=1
docker compose -f docker-compose.test.yml exec -T tests pytest || CATCH=1
docker compose -f docker-compose.test.yml exec -T tests black --check --diff src/ tests/ || CATCH=1
docker compose -f docker-compose.test.yml exec -T tests isort --check-only --diff src/ tests/ || CATCH=1
docker compose -f docker-compose.test.yml exec -T tests flake8 src/ tests/ || CATCH=1

if [ -z $PERSIST_CONTAINERS ]; then docker compose -f docker-compose.test.yml down || CATCH=1; fi

exit $CATCH