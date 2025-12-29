# Embedding Service Tests

Comprehensive test suite for the embedding service with **90% code coverage**.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py           # Pytest fixtures and configuration
├── test_model_manager.py # Unit tests for ModelManager (12 tests)
└── test_api.py           # API integration tests (21 tests)
```

## Running Tests

### Run all tests
```bash
uv run pytest
```

### Run with verbose output
```bash
uv run pytest -v
```

### Run with coverage
```bash
uv run pytest --cov=app --cov-report=html --cov-report=term
```

### Run specific test file
```bash
uv run pytest tests/test_api.py
uv run pytest tests/test_model_manager.py
```

### Run specific test class
```bash
uv run pytest tests/test_api.py::TestEmbedEndpoint
```

### Run specific test
```bash
uv run pytest tests/test_api.py::TestEmbedEndpoint::test_embed_single_text
```

### Skip slow tests
```bash
uv run pytest -m "not slow"
```

## Test Coverage

**Current Coverage: 90%**

| Module              | Coverage | Missing Lines         |
|---------------------|----------|-----------------------|
| app/config.py       | 100%     | -                     |
| app/models.py       | 100%     | -                     |
| app/model_manager.py| 98%      | Line 50               |
| app/main.py         | 78%      | Error handling blocks |
| **TOTAL**           | **90%**  | -                     |

## Test Categories

### Unit Tests (test_model_manager.py)
- ✅ Model loading and lazy loading
- ✅ Embedding generation (single & batch)
- ✅ Embedding consistency and similarity
- ✅ Model reloading
- ✅ Error handling for invalid models
- ✅ Normalization validation

### API Integration Tests (test_api.py)

#### Health & Info Endpoints
- ✅ Health check
- ✅ Model information

#### Embed Endpoint
- ✅ Single text embedding
- ✅ Empty text validation
- ✅ Missing field validation
- ✅ Invalid JSON handling
- ✅ Long text handling
- ✅ Special characters
- ✅ Embedding consistency

#### Batch Embed Endpoint
- ✅ Batch embedding (multiple texts)
- ✅ Single text in batch
- ✅ Empty list validation
- ✅ Large batch (100 texts)
- ✅ Mixed text lengths

#### Switch Model Endpoint
- ✅ Switch to same model
- ✅ Invalid model error handling
- ✅ Missing model name validation
- ✅ Switch to different model (marked as slow)

#### End-to-End Tests
- ✅ Complete workflow
- ✅ Concurrent requests

## Fixtures

Available in `conftest.py`:

- `test_model_name`: Default model for testing
- `model_manager`: Pre-loaded ModelManager instance
- `client`: FastAPI TestClient
- `sample_text`: Single text for testing
- `sample_texts`: Multiple texts for batch testing

## CI/CD Integration

Add to your CI pipeline:

```yaml
- name: Run tests
  run: |
    uv sync
    uv run pytest --cov=app --cov-report=xml --cov-report=term

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Writing New Tests

### Unit Test Example
```python
def test_new_feature(model_manager):
    """Test description."""
    result = model_manager.new_method()
    assert result == expected_value
```

### API Test Example
```python
def test_new_endpoint(client):
    """Test description."""
    response = client.post("/endpoint", json={"data": "value"})
    assert response.status_code == 200
    assert response.json()["key"] == "expected"
```

## Markers

- `@pytest.mark.slow` - Tests that take >5 seconds (e.g., model switching tests)

You can skip slow tests during development:
```bash
uv run pytest -m "not slow"
```

## Coverage Report

View HTML coverage report:
```bash
uv run pytest --cov=app --cov-report=html
open htmlcov/index.html  # macOS
```

## Continuous Improvement

Target: **95% coverage**

Areas to improve:
- Error handling in main.py lifespan
- Edge cases in model switching
- Exception handling in API endpoints

---

## Pytest Configuration Details

The test suite configuration in `pytest.ini`:

### Test Discovery

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
minversion = 7.0
```

- **testpaths**: Only look in `tests/` directory
- **python_files**: Files matching `test_*.py`
- **python_classes**: Classes starting with `Test`
- **python_functions**: Functions starting with `test_`
- **minversion**: Requires pytest 7.0+

### Command-line Options

```ini
addopts =
    --strict-markers
```

**Philosophy**: Minimal defaults. Only `--strict-markers` is enabled by default to catch typos in marker names.

**Common options you can add per run:**

```bash
# Verbose output (shows test names)
uv run pytest -v

# Short traceback format (less verbose errors)
uv run pytest --tb=short

# Long traceback format (detailed debugging)
uv run pytest --tb=long

# Suppress warnings
uv run pytest --disable-warnings

# Combine multiple options
uv run pytest -v --tb=short --disable-warnings

# Skip slow tests
uv run pytest -m "not slow" -v
```

### Why Minimal Configuration?

- **Flexibility**: Developers can choose their preferred output style
- **Transparency**: No hidden options affecting test behavior
- **Debugging**: Warnings and full tracebacks available when needed
- **Safety**: `--strict-markers` prevents typos in marker names
