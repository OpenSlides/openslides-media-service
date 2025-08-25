#!/bin/bash

# Executes all linters. Should errors occur, CATCH will be set to 1, causing an erroneous exit code.

echo "########################################################################"
echo "###################### Run Linters #####################################"
echo "########################################################################"

# Parameters
while getopts "l" FLAG; do
    case "${FLAG}" in
    l) LOCAL=true ;;
    *) echo "Can't parse flag ${FLAG}" && break ;;
    esac
done

# Setup

IMAGE_TAG=openslides-media-tests
DC="docker compose -f docker-compose.test.yml"

# Safe Exit
trap 'if [ -z "$LOCAL" ]; then docker compose -f docker-compose.test.yml down; fi' EXIT

# Execution
if [ -z "$LOCAL" ]
then
    # Setup
    make build-dev
    make build-tests
    docker build . -f tests/dummy_autoupdate/Dockerfile.dummy_autoupdate --tag openslides-media-dummy-autoupdate
	eval "$DC up -d"
	eval "$DC -T tests wait-for-it 'media:9006'"

    # Container Mode
    eval "$DC exec -T tests black --check --diff src/ tests/"
    eval "$DC exec -T tests isort --check-only --diff src/ tests/"
    eval "$DC exec -T tests flake8 src/ tests/"

else
    # Local Mode
    black --diff src/ tests/
    isort --diff src/ tests/
    flake8 src/ tests/
fi
