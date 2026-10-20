#!/usr/bin/env bash
#
# Prove that committed files alone reproduce the project.
# Clones into a temporary folder and runs tests, CLI, container.
# Run from an activated virtual environment so pytest and python resolve
# to the development interpreter.
#
set -euo pipefail

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

echo "== cloning into $work/clean"
git clone --quiet . "$work/clean"
cd "$work/clean"

echo "== pytest -q"
pytest -q

echo "== python -m femuralabs.toolkit.cli"
actual=$(PYTHONPATH=src python -m femuralabs.toolkit.cli)
echo "$actual"
expected="shape (z, y, x): (4, 6, 6)"
if [[ "$actual" != *"$expected"* ]]; then
    echo "FAIL: CLI output does not contain: $expected"
    exit 1
fi

echo "== docker build"
docker build -t toolkit-hello-clean .

echo "== docker run"
run_output=$(docker run --rm toolkit-hello-clean)
echo "$run_output"
if [[ "$run_output" != *"$expected"* ]]; then
    echo "FAIL: container output does not match"
    exit 1
fi

echo
echo "clean checkout: all checks passed"