#!/bin/bash

if [ -z "$VIRTUAL_ENV" ]; then
  . ./venv/bin/activate
fi

if [ -z "$AIB_PAC" ]; then
  echo -n "PAC: "
  read -s AIB_PAC
fi

export AIB_PAC

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
