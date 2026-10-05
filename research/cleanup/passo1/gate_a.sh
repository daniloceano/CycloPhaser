#!/usr/bin/env bash
# Passo 1 — gate (a): only C1 touches cyclophaser/ in this front.
#   bash research/cleanup/passo1/gate_a.sh > research/cleanup/passo1/gate_a.txt
# Expected: exactly one line, the C1 commit.
set -eu
cd "$(git rev-parse --show-toplevel)"
git fetch -q origin develop-v2.1
echo "HEAD: $(git rev-parse --short HEAD)"
echo "origin/develop-v2.1: $(git rev-parse --short origin/develop-v2.1)"
echo "\$ git log --format=%h origin/develop-v2.1..HEAD -- cyclophaser/"
git log --format=%h origin/develop-v2.1..HEAD -- cyclophaser/
echo "\$ git log --format='%h %s' origin/develop-v2.1..HEAD   # all commits of the front, for context"
git log --format='%h %s' origin/develop-v2.1..HEAD
