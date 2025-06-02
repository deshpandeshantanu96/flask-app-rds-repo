#!/bin/bash

APP_URL=$1

echo "Testing app at $APP_URL"

# Simple GET request to homepage
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$APP_URL/")

if [ "$HTTP_STATUS" -eq 200 ]; then
  echo "✅ App is reachable and returned HTTP 200"
  exit 0
else
  echo "❌ App returned HTTP status $HTTP_STATUS"
  exit 1
fi
