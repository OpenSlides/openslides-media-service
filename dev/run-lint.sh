#!/bin/bash

# Executes all linters. Should errors occur, CATCH will be set to 1, causing an erroneous exit code.

echo "########################################################################"
echo "###################### Run Linters #####################################"
echo "########################################################################"

# Parameters
while getopts "lscp" FLAG; do
    case "${FLAG}" in
    l) LOCAL=true ;;
    s) SKIP_BUILD=true ;;
    c) SKIP_CONTAINER_UP=true ;;
    p) PERSIST_CONTAINERS=true ;;
    *) echo "Can't parse flag ${FLAG}" && break ;;
    esac
done

# Setup
IMAGE_TAG=openslides-media-tests
CATCH=0
DC="docker compose -f docker-compose.test.yml"

# Optionally build image
if [ -z "$SKIP_BUILD" ]
then
    make build-dev || CATCH=1
    make build-tests || CATCH=1
    docker build . -f tests/dummy_autoupdate/Dockerfile.dummy_autoupdate --tag openslides-media-dummy-autoupdate || CATCH=1
fi

if [ -z "$SKIP_CONTAINER_UP" ]
then
	eval "$DC up -d" || CATCH=1
	eval '$DC -T tests wait-for-it "media:9006"' || CATCH=1
fi

# Execution
if [ -z "$LOCAL" ]
then
    # Container Mode
    eval "$DC exec -T tests black --check --diff src/ tests/" || CATCH=1
    eval "$DC exec -T tests isort --check-only --diff src/ tests/" || CATCH=1
    eval "$DC exec -T tests tests flake8 src/ tests/" || CATCH=1

else
    # Local Mode
    black --diff src/ tests/
    isort --diff src/ tests/
    flake8 src/ tests/
fi

if [ -z "$PERSIST_CONTAINERS" ] && [ -z "$SKIP_CONTAINER_UP" ]; then docker stop autoupdate-test && docker rm autoupdate-test || CATCH=1; fi

exit $CATCH