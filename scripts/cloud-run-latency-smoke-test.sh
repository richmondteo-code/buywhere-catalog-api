#!/usr/bin/env bash
# scripts/cloud-run-latency-smoke-test.sh
# Lightweight bash smoke test for Cloud Run deployment health.
# Used by deploy-cloud-run-staging.yml and deploy-cloud-run-production.yml.

set -e

API_BASE_URL="${1:-${API_BASE_URL:-}}"

if [ -z "$API_BASE_URL" ]; then
  echo "ERROR: API_BASE_URL not provided as argument or env var"
  exit 1
fi

echo "=== Cloud Run Latency Smoke Test ==="
echo "Target: $API_BASE_URL"
echo "Running at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

ENDPOINTS=(
  "/health"
)

PASSED=0
FAILED=0

for endpoint in "${ENDPOINTS[@]}"; do
  url="${API_BASE_URL}${endpoint}"
  echo -n "GET $endpoint ... "

  # Measure latency with curl
  start_ns=$(date +%s%N)
  http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url")
  end_ns=$(date +%s%N)

  latency_ms=$(( (end_ns - start_ns) / 1000000 ))

  if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 500 ]; then
    echo "OK (${latency_ms}ms, status=$http_code)"
    PASSED=$((PASSED + 1))
  else
    echo "FAIL (status=$http_code, latency=${latency_ms}ms)"
    FAILED=$((FAILED + 1))
  fi
done

echo ""
echo "Results: $PASSED passed, $FAILED failed"
echo ""

# Run 5 quick latency samples for basic stats
echo "=== Latency samples (n=5) ==="
total_latency=0
max_latency=0
latencies=()

for i in {1..5}; do
  start_ns=$(date +%s%N)
  curl -s -o /dev/null --max-time 10 "${API_BASE_URL}/health" > /dev/null 2>&1 || true
  end_ns=$(date +%s%N)
  lat_ms=$(( (end_ns - start_ns) / 1000000 ))
  latencies+=($lat_ms)
  total_latency=$((total_latency + lat_ms))
  if [ $lat_ms -gt $max_latency ]; then
    max_latency=$lat_ms
  fi
  echo "  sample $i: ${lat_ms}ms"
done

avg_latency=$((total_latency / 5))
echo ""
echo "Average latency: ${avg_latency}ms"
echo "Max latency: ${max_latency}ms"

# Calculate P95 manually from 5 samples (approximate, small sample)
sorted=($(for l in "${latencies[@]}"; do echo "$l"; done | sort -n))
p95_idx=$(( (5 * 95 / 100) - 1 ))
p95_latency=${sorted[$p95_idx]}
echo "P95 latency: ${p95_latency}ms"
echo ""
echo "=== Smoke Test Summary ==="
echo "Average latency: ${avg_latency}ms"
echo "P95 latency: ${p95_latency}ms"
echo "Max latency: ${max_latency}ms"

if [ $FAILED -gt 0 ]; then
  echo "STATUS: FAILED"
  exit 1
fi

if [ $avg_latency -gt 2000 ]; then
  echo "WARNING: Average latency exceeds 2000ms"
fi

echo "STATUS: PASSED"
exit 0