#!/bin/sh
case "$1" in
  *username*) echo "wk123-11" ;;
  *password*) cat /home/wk/ai-tool-review/scripts/.ghtoken ;;
  *) exit 1 ;;
esac
