#!/bin/bash
# GIT_ASKPASS helper: output token from .ghtoken file
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
case "$1" in
  *Username*|*username*)
    echo "wk123-11"
    ;;
  *Password*|*password*|*Token*|*token*)
    cat "$SCRIPT_DIR/.ghtoken"
    ;;
esac
