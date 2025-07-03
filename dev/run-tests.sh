#!/bin/bash

# Executes all tests. Should errors occur, CATCH will be set to 1, causing an erroneous exit code.

echo "########################################################################"
echo "###################### Run Tests and Linters ###########################"
echo "########################################################################"

# Parameters
while getopts "p" FLAG; do
    case "${FLAG}" in
    p) PERSIST_CONTAINERS=true ;;
    s) SKIP_BUILD=true ;;
    *) echo "Can't parse flag ${FLAG}" && break ;;
    esac
done

# Setup
CATCH=0
LOCAL_PWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Builds
if [ -z "$SKIP_BUILD" ]
then
    make build-dev || CATCH=1
    make build-tests || CATCH=1
    docker build . -f tests/dummy_autoupdate/Dockerfile.dummy_autoupdate --tag openslides-media-dummy-autoupdate || CATCH=1
fi

# Execution
docker compose -f docker-compose.test.yml up -d || CATCH=1
docker compose -f docker-compose.test.yml exec -T tests wait-for-it "media:9006" || CATCH=1
docker compose -f docker-compose.test.yml exec -T tests pytest || CATCH=1

# Linters
bash "$LOCAL_PWD"/run-lint.sh -s -c || CATCH=1

if [ -z "$PERSIST_CONTAINERS" ]; then docker compose -f docker-compose.test.yml down || CATCH=1; fi

exit $CATCH