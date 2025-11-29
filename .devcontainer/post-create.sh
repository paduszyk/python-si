#!/usr/bin/env bash

set -e

git clean -dxf

npm clean-install
uv sync --all-groups --locked

npx --no-install lefthook install --force
