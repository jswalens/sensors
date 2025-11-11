#!/usr/bin/env bash
set -euo pipefail

# Home Assistant Sensor Uploader
#
# This script reads data from the MH-Z19 CO₂ sensor (every 2 minutes) and
# SDS-011 sensor (every 30 minutes), logs it to local log files, and sends it
# to Home Assistant.
#
# Requirements: bash, curl, jq
#
# Create a .env file in the same directory containing:
#     HA_URL=http://homeassistant.local:8123
#     HA_TOKEN=your_long_lived_access_token

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.env"

LOG_DIR="$(dirname "$0")"
MHZ19_LOG="$LOG_DIR/mh-z19.log"
SDS011_LOG="$LOG_DIR/sds-011.log"

# Helper for logging during debugging.
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# Helper to send data to Home Assistant.
post_to_ha() {
  local entity_id="$1"
  local state="$2"
  local attr_json="$3"

  # For debugging, change -f to -v
  if ! curl -s -f -X POST \
    -H "Authorization: Bearer $HA_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"state\": \"$state\", \"attributes\": $attr_json}" \
    "$HA_URL/api/states/$entity_id" >/dev/null; then
    log "Warning: failed to post $entity_id to Home Assistant"
  fi
}

# Read MH-Z19 sensor every 2 minutes.
read_mhz19() {
  log "Starting MH-Z19 CO₂ sensor loop"
  while true; do
    # Example output: {"time": "2025-11-11T00:41:27+0100", "co2": 558, "temperature": 26, "TT": 66, "SS": 0, "Uh": 52, "Ul": 1}
    output=$(sudo python3 mh-z19.py --all | tee -a "$MHZ19_LOG" || true)
    timestamp=$(echo "$output" | jq -r '.time // empty')
    co2=$(echo "$output" | jq -r '.co2 // empty')
    temp=$(echo "$output" | jq -r '.temperature // empty')
    log "CO₂: $co2 ppm; temperature: $temp °C (timestamp $timestamp)"

    if [[ -n "$co2" ]]; then
      post_to_ha "sensor.mhz19_co2" "$co2" '{"friendly_name": "CO₂", "icon": "mdi:molecule-co2", "device_class": "co2", "unit_of_measurement":"ppm", "state_class": "measurement"}'
    fi
    if [[ -n "$temp" ]]; then
      post_to_ha "sensor.mhz19_temperature" "$temp" '{"friendly_name": "temperature", "icon": "mdi:temperature-celsius", "device_class": "temperature", "unit_of_measurement":"°C", "state_class": "measurement"}'
      # TODO does this make sense, or should this be an attribute of the one above?
    fi

    sleep 2m
  done
}

# Read SDS011 sensor every 30 minutes.
read_sds011() {
  log "Starting SDS-011 dust sensor loop"
  while true; do
    # Example output: 2025-11-11T00:40:22+0100,1.6,3.4
    output=$(python3 sds-011.py | tee -a "$SDS011_LOG" || true)
    line=$(echo "$output" | tail -n1)

    # Split CSV fields
    IFS=',' read -r timestamp pm25 pm10 <<< "$line"
    log "PM2.5: $pm25 µg/m³; PM10: $pm10 µg/m³ (timestamp $timestamp)"

    if [[ -n "$pm25" ]]; then
      post_to_ha "sensor.sds011_pm25" "$pm25" '{"friendly_name": "PM2.5", "icon": "mdi:air-filter", "device_class": "pm25", "unit_of_measurement":"µg/m³", "state_class": "measurement"}'
    fi
    if [[ -n "$pm10" ]]; then
      post_to_ha "sensor.sds011_pm10" "$pm10" '{"friendly_name": "PM10", "icon": "mdi:air-filter", "device_class": "pm10", "unit_of_measurement":"µg/m³", "state_class": "measurement"}'
    fi

    sleep 30m
  done
}

main() {
  # Run both loops concurrently
  read_mhz19 &
  read_sds011 &
  wait
}

main
