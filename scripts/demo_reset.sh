#!/usr/bin/env bash
# Demo preflight: check the API, log in as the OSINT service account, put the
# demo camera back to Dormant, and print the commands that drive the demo.
# Run with: bash scripts/demo_reset.sh
#
# Reads BASE_URL, OSINT_API_USERNAME, OSINT_API_PASSWORD, CAMERA_ID,
# NTFY_SERVER, NTFY_TOPIC, and RSS_FEED_URL from the environment (see
# ai-brain/.env.example). Credentials and the access token never appear in
# output or in curl's argument list. Needs curl and jq.
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
BASE_URL="${BASE_URL%/}"
CAMERA_ID="${CAMERA_ID:-1}"
NTFY_SERVER="${NTFY_SERVER:-https://ntfy.sh}"
NTFY_SERVER="${NTFY_SERVER%/}"
NTFY_TOPIC="${NTFY_TOPIC:-}"
RSS_FEED_URL="${RSS_FEED_URL:-http://localhost:8001/feed.xml}"
NTFY_PLACEHOLDER_TOPIC="heimdall-demo-change-me"
DEMO_REPORT="Armed man with a gun at the north gate"

TOKEN=""
STATUS=""
BODY=""

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

ok() {
  printf 'OK:   %s\n' "$*"
}

warn() {
  printf 'WARN: %s\n' "$*"
}

require_tools() {
  local tool
  for tool in curl jq; do
    command -v "$tool" >/dev/null 2>&1 || fail "$tool is not installed."
  done
  if [[ ! "$CAMERA_ID" =~ ^[1-9][0-9]*$ ]]; then
    fail "CAMERA_ID must be a positive integer."
  fi
}

auth_header() {
  if [[ -n "$TOKEN" ]]; then
    printf 'Authorization: Bearer %s\n' "$TOKEN"
  fi
}

# request PATH [curl args...]: call the API and set STATUS and BODY.
request() {
  local path=$1 response
  shift
  response=$(curl -sS --max-time 10 -H 'Accept: application/json' \
    -H @<(auth_header) -w '\n%{http_code}' "$@" "$BASE_URL$path") \
    || fail "Cannot reach the API at $BASE_URL. Start it with: docker compose up -d"
  STATUS=${response##*$'\n'}
  BODY=${response%$'\n'*}
}

# json_field FILTER: read one field from BODY, empty when missing or invalid.
json_field() {
  printf '%s' "$BODY" | jq -r "$1 // empty" 2>/dev/null || true
}

login_body() {
  jq -n '{username: env.OSINT_API_USERNAME, password: env.OSINT_API_PASSWORD}'
}

dormant_body() {
  jq -n --argjson fps "$1" --arg resolution "$2" \
    '{mode: "Dormant", fps: $fps, resolution: $resolution}'
}

check_health() {
  request /health
  if [[ "$STATUS" != 200 || "$(json_field .status)" != ok ]]; then
    fail "GET /health returned HTTP $STATUS. Check the api and db containers."
  fi
  ok "API is healthy at $BASE_URL (database $(json_field .database))."
}

log_in() {
  if [[ -z "${OSINT_API_USERNAME:-}" || -z "${OSINT_API_PASSWORD:-}" ]]; then
    fail "Set OSINT_API_USERNAME and OSINT_API_PASSWORD in the environment."
  fi
  request /auth/login -X POST -H 'Content-Type: application/json' \
    --data-binary @- < <(login_body)
  if [[ "$STATUS" != 200 ]]; then
    fail "Login failed (HTTP $STATUS). Check the OSINT service account."
  fi
  TOKEN=$(json_field .access_token)
  [[ -n "$TOKEN" ]] || fail "Login response did not include an access token."
  ok "Logged in as the OSINT service account."
}

reset_camera() {
  local path="/camera-states/$CAMERA_ID" mode fps resolution
  request "$path"
  if [[ "$STATUS" == 404 ]]; then
    fail "Camera $CAMERA_ID does not exist. Seed it with: docker compose exec api python -m backend.app.seed"
  fi
  [[ "$STATUS" == 200 ]] || fail "GET $path returned HTTP $STATUS."
  mode=$(json_field .mode)
  fps=$(json_field .fps)
  resolution=$(json_field .resolution)
  if [[ ! "$fps" =~ ^[1-9][0-9]*$ || -z "$resolution" ]]; then
    fail "GET $path did not return a usable fps and resolution."
  fi
  ok "Camera $CAMERA_ID is $mode at $fps fps, $resolution."

  request "$path" -X PUT -H 'Content-Type: application/json' \
    --data-binary @- < <(dormant_body "$fps" "$resolution")
  if [[ "$STATUS" != 200 || "$(json_field .mode)" != Dormant ]]; then
    fail "PUT $path returned HTTP $STATUS; camera $CAMERA_ID was not reset."
  fi
  ok "Camera $CAMERA_ID set to Dormant (kept $fps fps, $resolution)."
}

print_ntfy_step() {
  local topic=$NTFY_TOPIC
  if [[ -z "$topic" || "$topic" == "$NTFY_PLACEHOLDER_TOPIC" ]]; then
    warn "NTFY_TOPIC is unset or the placeholder. Pick a unique topic; public ntfy topics are readable by anyone."
    topic="${topic:-<your-topic>}"
  fi
  printf '     curl -d "%s" %s/%s\n' "$DEMO_REPORT" "$NTFY_SERVER" "$topic"
}

print_rss_step() {
  if [[ "$RSS_FEED_URL" == */feed.xml ]]; then
    printf '     curl -d "text=%s" %s/items\n' "$DEMO_REPORT" "${RSS_FEED_URL%/feed.xml}"
  else
    printf '     Publish the same report to %s\n' "$RSS_FEED_URL"
  fi
}

print_demo_steps() {
  printf '\nDemo steps, each in its own terminal from the repository root:\n'
  printf '  1. RSS demo feed:  python ai-brain/demo_feed.py\n'
  printf '  2. OSINT loop:     FEATURE_LIVE_OSINT=true python ai-brain/main.py\n'
  printf '     (needs GROQ_API_KEY in ai-brain/.env)\n'
  printf '  3. Send the same report from both sources within CORROBORATION_WINDOW_SECONDS:\n'
  print_ntfy_step
  print_rss_step
  printf '  Camera %s turns Active when both reports get the same object class.\n' "$CAMERA_ID"
}

main() {
  require_tools
  check_health
  log_in
  reset_camera
  print_demo_steps
}

main "$@"
