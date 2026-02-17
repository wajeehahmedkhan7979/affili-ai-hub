# Testing Guide

## Running Tests

### Prerequisites
- Virtual environment activated
- Dependencies installed: `pip install -r requirements.txt`

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test
```bash
pytest tests/test_api.py::test_health_check
```

### Run Tests in Verbose Mode
```bash
pytest -v
```

### Run Only Unit Tests
```bash
pytest tests/ -m "not integration"
```

## Test Structure

- `conftest.py`: Pytest configuration and shared fixtures
  - `client`: FastAPI test client
  - `db_session`: SQLite test database session
  - `engine`: SQLAlchemy engine for tests

- `test_api.py`: API endpoint tests
  - Health checks
  - Program CRUD
  - Application lifecycle
  - Task management and polling
  - Response pool operations

## Database for Tests

Tests use an in-memory SQLite database that is created and destroyed for each test session.
This ensures tests are isolated and fast.

## Coverage Target

Aim for:
- Core CRUD operations: 90%+ coverage
- Task lifecycle: 85%+ coverage
- Service layer: 80%+ coverage

## Continuous Integration

For CI/CD (GitHub Actions, GitLab CI):
```bash
pip install -r requirements.txt
pytest --cov=app --cov-report=term --cov-report=xml
