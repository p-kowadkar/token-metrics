#!/bin/bash
# Test runner script for Token Metrics Monitor

set -e

echo "🧪 Running Token Metrics Monitor Test Suite..."
echo ""

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -q -r tests/requirements-test.txt

# Run tests with coverage
echo ""
echo "🔍 Running tests with coverage..."
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

echo ""
echo "✅ Test suite complete!"
echo ""
echo "Coverage report saved to htmlcov/index.html"
