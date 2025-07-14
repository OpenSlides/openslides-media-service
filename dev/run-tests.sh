#!/bin/bash

# Executes all tests. Should errors occur, CATCH will be set to 1, causing an erroneous exit code.

echo "########################################################################"
echo "###################### Run Tests and Linters ###########################"
echo "########################################################################"

# Parameters
while getopts "s" FLAG; do
    case "${FLAG}" in
    s) SKIP_BUILD=true ;;
    *) echo "Can't parse flag ${FLAG}" && break ;;
    esac
done

# Setup
LOCAL_PWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Safe Exit
trap 'docker compose -f docker-compose.test.yml down' EXIT

# Builds
if [ -z "$SKIP_BUILD" ]
then
    make build-dev
    make build-tests
    docker build . -f tests/dummy_autoupdate/Dockerfile.dummy_autoupdate --tag openslides-media-dummy-autoupdate
fi

# Execution
docker compose -f docker-compose.test.yml up -d
docker compose -f docker-compose.test.yml exec -T tests wait-for-it "media:9006"
docker compose -f docker-compose.test.yml exec -T tests pytest

# Linters
bash "$LOCAL_PWD"/run-lint.sh -s -c