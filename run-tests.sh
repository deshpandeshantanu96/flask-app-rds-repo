#!/bin/bash
set -eo pipefail

APP_URL=$1
MAX_RETRIES=5
RETRY_DELAY=5

echo "🔍 Testing application at $APP_URL"

# Retry logic for connection issues
for i in $(seq 1 $MAX_RETRIES); do
  echo "Attempt $i/$MAX_RETRIES"
  
  # Get HTTP status and full response
  RESPONSE=$(curl -s -w "\n%{http_code}" --connect-timeout 10 "$APP_URL/health")
  HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
  BODY=$(echo "$RESPONSE" | sed '$d')

  if [ "$HTTP_STATUS" -eq 200 ]; then
    echo "✅ Health check passed"
    echo "Response: $BODY"
    exit 0
  else
    echo "⚠️ Attempt $i failed: HTTP $HTTP_STATUS"
    echo "Response: $BODY"
    [ $i -lt $MAX_RETRIES ] && sleep $RETRY_DELAY
  fi
done

echo "❌ All attempts failed"
exit 1