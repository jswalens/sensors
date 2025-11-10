#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="$(dirname "$0")"
MHZ19_LOG="$LOG_DIR/mh-z19.log"
SDS011_LOG="$LOG_DIR/sds-011.log"

read_mhz19() {
  while true; do
    sudo python3 mh-z19.py --all | tee -a "$MHZ19_LOG"
    sleep 2m
  done
}

read_sds011() {
  while true; do
    python3 sds-011.py | tee -a "$SDS011_LOG"
    sleep 30m
  done
}

main() {
  read_mhz19 &
  read_sds011 &
  wait
}

main
