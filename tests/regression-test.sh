#!/usr/bin/env bash
#
# Regression test: runs the unit tests and the acceptance tests locally, the latter against
# GraphDB 10, which needs no licence. Builds the three images, runs the unit tests in the
# application image, runs the two acceptance passes that CI runs (Completions API, then Responses
# API) and tears everything down again.
#
#   tests/regression-test.sh                   # everything; about six minutes once the images are cached
#   tests/regression-test.sh -k test_health    # arguments are passed on to pytest for the acceptance tests
#
# Settings are environment variables:
#   GRAPHDB_VERSION   tag of the ontotext/graphdb image to test against   [10.8.14]
#
# Needs Docker with about 15 GB of free disk. Below that GraphDB reports its storage as critically
# low, the chatbot's health becomes WARNING, and the tests that expect OK fail.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
COMPOSE="$HERE/acceptance_tests/docker-compose/docker-compose.yaml"
GRAPHDB_VERSION="${GRAPHDB_VERSION:-10.8.14}"

command -v docker > /dev/null || { echo "ERROR: docker is not installed" >&2; exit 2; }

cd "$ROOT"

# The containers have fixed names, so two runs cannot share a machine: the second would recreate
# the containers under the first.
if [ -n "$(docker ps --quiet --filter label=com.docker.compose.service=talk2powersystem-acceptance-tests)" ]; then
  echo "ERROR: an acceptance test run is already in progress" >&2
  exit 2
fi

manifest_existed=0
[ ! -f git-manifest.yaml ] || manifest_existed=1

cleanup() {
  docker compose -f "$COMPOSE" down -v --remove-orphans > /dev/null 2>&1 || true
  [ "$manifest_existed" = 1 ] || rm -f git-manifest.yaml
}
trap cleanup EXIT

step() {
  printf '\n== %s ==\n' "$1"
}

# When a pass fails, the cause is often a nearly full Docker disk and not the code under test.
explain_failure() {
  local storage
  storage="$(docker exec graphdb curl -s 'http://localhost:7200/repositories/cim/health?passive=5' 2> /dev/null |
    grep -o 'The usable space on the device is [^"]*' || true)"
  if [ -n "$storage" ]; then
    echo "NOTE: GraphDB reports: $storage"
    echo "      This turns the chatbot's health into WARNING and fails the tests that expect OK."
  fi
}

results=()
failed=0

# The unit tests run inside the application image, so against the dependencies that the image
# ships with. The image has no test runner; the versions are those of the test group in pyproject.toml.
run_unit_tests() {
  step "Unit tests"
  if docker run --rm --volume "$ROOT/tests:/code/tests:ro" talk2powersystem sh -c '
      pip install --quiet --disable-pip-version-check --root-user-action=ignore "pytest>=9.0.3,<10" "pytest-asyncio>=1,<2" &&
      python -m pytest tests/unit_tests/'; then
    results+=("PASS  Unit tests")
  else
    results+=("FAIL  Unit tests")
    failed=1
  fi
}

# run_pass NAME SETTING [PYTEST_ARGS...]: one pytest run, with the chatbot started under SETTING.
run_pass() {
  local name="$1" setting="$2"
  shift 2
  step "$name"
  if env -u LLM_SEED -u LLM_USE_RESPONSES_API "$setting" \
    docker compose -f "$COMPOSE" run --rm talk2powersystem-acceptance-tests \
    poetry run pytest tests/acceptance_tests/ "$@"; then
    results+=("PASS  $name")
  else
    results+=("FAIL  $name")
    failed=1
    explain_failure
  fi
}

# A stack left behind by an earlier run would be reused with its old images.
docker compose -f "$COMPOSE" down -v --remove-orphans > /dev/null 2>&1 || true

step "Building the application image"
bash ./docker/generate-manifest.sh > /dev/null 2>&1 || { echo "ERROR: docker/generate-manifest.sh failed" >&2; exit 2; }
docker buildx build --file docker/Dockerfile --tag talk2powersystem .

run_unit_tests

step "Building the acceptance tests image"
docker buildx build --file tests/acceptance_tests/docker-compose/DockerfileAcceptanceTests --tag talk2powersystem-acceptance-tests .

step "Building the GraphDB $GRAPHDB_VERSION image"
docker buildx build --build-arg "GRAPHDB_VERSION=$GRAPHDB_VERSION" \
  --file tests/acceptance_tests/docker-compose/DockerfileGraphDB --tag graphdb .

run_pass "Acceptance tests, Completions API" LLM_SEED=1 "$@"
run_pass "Acceptance tests, Responses API" LLM_USE_RESPONSES_API=true "$@"

step "Result on GraphDB $GRAPHDB_VERSION"
printf '%s\n' "${results[@]}"
if [ "$failed" = 1 ]; then
  echo "The application log is in tests/acceptance_tests/docker-compose/logs/."
  exit 1
fi
