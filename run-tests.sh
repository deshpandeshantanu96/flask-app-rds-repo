#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

APP_URL=$1

echo "🚀 Starting tests for application at $APP_URL"

# 1. Verify we received a URL parameter
if [ -z "$APP_URL" ]; then
  echo "❌ Error: No URL provided"
  echo "Usage: ./run-tests.sh <application-url>"
  exit 1
fi

# 2. Check if curl is available
if ! command -v curl &> /dev/null; then
  echo "❌ Error: curl is not installed"
  exit 1
fi

# 3. Test basic connectivity (with timeout)
echo "🔍 Testing basic connectivity..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$APP_URL/")

if [ "$HTTP_STATUS" -eq 200 ]; then
  echo "✅ Success: App returned HTTP 200"
else
  echo "❌ Failed: App returned HTTP $HTTP_STATUS"
  
  # Additional debugging info
  echo "🛠️ Debug information:"
  echo "Trying verbose curl..."
  curl -v "$APP_URL/" || true
  exit 1
fi

# 4. Test API endpoints (example - customize for your app)
echo "🔍 Testing API endpoints..."
API_RESPONSE=$(curl -s --connect-timeout 10 "$APP_URL/api/health")

if [[ "$API_RESPONSE" =~ "ok" ]]; then
  echo "✅ API health check passed"
else
  echo "❌ API health check failed"
  echo "Response: $API_RESPONSE"
  exit 1
fi

# 5. Add more specific test cases for your application here
# Example:
# echo "🔍 Testing database connection..."
# DB_STATUS=$(curl -s "$APP_URL/api/db-status")
# ...

echo "🎉 All tests passed successfully!"
exit 0