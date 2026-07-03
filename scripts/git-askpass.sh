#!/bin/sh
case "$1" in
  *username*)
    echo "wk123-11"
    ;;
  *password*|*token*)
    cat /home/wk/ai-tool-review/scripts/.ghtoken
    ;;
esac