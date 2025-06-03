#!/bin/bash

# Executes all tests. Should errors occur, CATCH will be set to 1, causing an erronous exit code.

echo "########################################################################"
echo "###################### Start full system tests #########################"
echo "########################################################################"

CATCH=0
PERSIST_CONTAINERS=$2
CHOWN=$1

# Builds
make build-dev || CATCH=1
make build-test || CATCH=1
docker build . -f tests/dummy_autoupdate/Dockerfile.dummy_autoupdate --tag openslides-media-dummy-autoupdate || CATCH=1

# Run Tests
docker compose -f docker-compose.test.yml up -d || CATCH=1
docker compose -f docker-compose.test.yml exec -T tests wait-for-it "media:9006" || CATCH=1
docker compose -f docker-compose.test.yml exec -T tests pytest || CATCH=1

if [ -z $PERSIST_CONTAINERS ]; then docker compose -f docker-compose.test.yml down || CATCH=1; fi

exit $CATCH