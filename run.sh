#!/bin/bash

while :; do
  echo
  date
  if python -m aib_scraper >DIFF.diff; then
    echo no diff
  else
    cat DIFF.diff
    telegram_send <DIFF.diff
  fi
  sleep 600
done
