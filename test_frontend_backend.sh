#!/bin/bash

# Test script to verify frontend and backend connectivity
# NOTE: Admin credentials are configured via environment variables, not hardcoded

FRONTEND_URL="https://respectful-strength-production-ef28.up.railway.app"
BACKEND_URL="https://coredentist-production.up.railway.app"
API_URL="$BACKEND_URL/api/v1"

echo "=== CoreDent Deployment Test ==="
echo ""

# Test 1: Backend health check
echo "1. Testing backend health check..."
curl -s -o /dev/null -w "Status: %{http_code}\n" "$BACKEND_URL/health"
echo ""

# Test 2: Frontend accessibility
echo "2. Testing frontend accessibility..."
curl -s -o /dev/null -w "Status: %{http_code}\n" "$FRONTEND_URL"
echo ""

# Test 3: Backend API root
echo "3. Testing backend API root..."
curl -s -o /dev/null -w "Status: %{http_code}\n" "$API_URL"
echo ""

# Test 4: Health endpoint (no auth required)
echo "4. Testing API health endpoint..."
curl -s "$API_URL/health/" -w "\nStatus: %{http_code}\n" | head -5
echo ""

echo "=== Test Complete ==="
echo "Note: Authentication tests require credentials from environment variables."
echo "Set ADMIN_EMAIL and ADMIN_PASSWORD to run login tests."