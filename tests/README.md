# Test Suite

This directory contains comprehensive tests for the Token Metrics Monitor application.

## Test Coverage

- **test_ingest.py**: Tests for data ingestion, API fetching, retry logic, and error handling
- **test_anomaly_detector.py**: Tests for anomaly detection algorithms and threshold checks
- **test_api.py**: Tests for FastAPI endpoints and HTTP responses
- **test_notifications.py**: Tests for Slack notification integration

## Running Tests

### Quick Start

```bash
# From project root
./run_tests.sh
```

### Manual Execution

```bash
# Install test dependencies
pip install -r tests/requirements-test.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_ingest.py -v

# Run specific test
pytest tests/test_ingest.py::TestProtocolDataFetcher::test_fetch_with_retry_success -v
```

## Test Structure

Each test file follows the same pattern:

1. **Setup**: Mock dependencies and fixtures
2. **Execute**: Call the function/method being tested
3. **Assert**: Verify expected behavior

## Mocking

Tests use `unittest.mock` to mock external dependencies:
- Database connections
- HTTP requests
- Environment variables
- Time-dependent functions

## Coverage Goals

- **Target**: >80% code coverage
- **Critical paths**: 100% coverage for error handling and retry logic
- **Edge cases**: Tests for timeouts, malformed data, and failures
