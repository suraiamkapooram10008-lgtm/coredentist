#!/bin/bash
# Quick test runner for coverage improvement
# Run this script to execute all enhanced tests

echo "🧪 Running enhanced tests for coverage improvement..."
echo "=================================================="

cd "$(dirname "$0")" || exit 1

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
fi

# Run tests with coverage
echo "📊 Running tests with coverage..."
python -m pytest tests/test_appointments_enhanced.py tests/test_subscriptions_enhanced.py tests/test_treatment_enhanced.py tests/test_billing_enhanced.py tests/test_imaging_enhanced.py -v --tb=short --timeout=60 2>&1 | head -100

echo ""
echo "📈 Generating coverage report..."
python -m pytest tests/test_appointments_enhanced.py tests/test_subscriptions_enhanced.py --cov=app --cov-report=term-missing --timeout=60 2>&1 | grep -A 50 "app/api"

echo ""
echo "✅ Test run complete!"
echo "Check the output above for coverage numbers."
