
# fastapptest

**fastapptest** is a production-ready **FastAPI test automation framework** designed for CI/CD pipelines, batch API testing, and interactive manual testing.  
It automatically scans FastAPI projects, extracts endpoints and Pydantic models, generates request payloads, executes tests, validates responses, and produces structured reports.

The library is built to test **real FastAPI applications** without requiring any changes to the application source code.

---

## Key Features

- Automatic FastAPI project scanning
- Endpoint discovery across routers and modules
- Pydantic request and response model extraction
- Automatic payload generation for write operations
- **Interactive manual endpoint testing**
- CI/CD-style full test execution
- Batch testing using predefined JSON payloads
- HTTP status code validation
- Response schema validation
- JWT, API key, and custom header authentication support
- JSON-based test reports
- Terminal test summary output
- CLI-first design with optional programmatic usage

---

## Installation

Install from PyPI:

```bash
pip install fastapptest
````

Ensure that your FastAPI project and all its dependencies are installed in the same environment.

---

## How fastapptest Works

fastapptest operates directly on a FastAPI project directory.

It performs the following steps:

1. Scans the project for FastAPI applications and routers
2. Extracts all registered API endpoints
3. Identifies HTTP methods, paths, and parameters
4. Extracts Pydantic request and response models
5. Generates payloads for POST, PUT, and PATCH requests
6. Executes HTTP requests against the running application
7. Validates status codes and response schemas
8. Generates structured JSON reports and terminal summaries

No instrumentation or test-specific code is required inside the FastAPI application.

---

## CLI Usage

fastapptest provides three primary CLI testing modes.

---

## Manual Testing (Interactive)

The **manual testing mode** allows interactive testing of individual endpoints in a FastAPI project.
This mode is useful for exploratory testing, debugging, and validating endpoint behavior during development.

```bash
manual_test <project_root> [--auth <auth_json>]
```

### Features

* Lists all discovered endpoints
* Allows selection of a specific endpoint to test
* Prompts for path parameters, query parameters, headers, and request body
* Sends requests interactively
* Displays response status codes and response bodies immediately

### Example

```bash
manual_test ./my_fastapi_project --auth '{"Authorization":"Bearer <token>"}'
```

Authentication headers are automatically applied to all requests during the interactive session.

---

## CI/CD Testing

Run a full automated test suite against a FastAPI project:

```bash
ci_test <project_root> [--output <output_dir>] [--auth <auth_json>] [--fail-fast]
```

### Arguments

* `project_root`
  Root directory of the FastAPI project

* `--output`
  Directory to store the CI/CD report (default: `ci_reports`)

* `--auth`
  Optional JSON string for authentication headers
  Example:

  ```json
  {"Authorization": "Bearer <token>"}
  ```

* `--fail-fast`
  Stop execution on the first failure

### Example

```bash
ci_test ./my_fastapi_project --output ci_reports --auth '{"Authorization":"Bearer <token>"}'
```

---

## Batch Testing

Run targeted tests using predefined payloads:

```bash
batch_test <project_root> <batch_file> [--output <output_file>] [--auth <auth_json>]
```

### Arguments

* `project_root`
  Root directory of the FastAPI project

* `batch_file`
  JSON file defining test requests

* `--output`
  Path to save the batch test report
  Default: `batch_reports/batch_test_report.json`

* `--auth`
  Optional authentication headers

### Batch File Format

```json
[
  {
    "path": "/users",
    "method": "POST",
    "body": {
      "username": "test",
      "email": "test@example.com"
    }
  },
  {
    "path": "/users/{id}",
    "method": "GET",
    "path_params": {
      "id": 1
    }
  }
]
```

---

## Programmatic Usage

fastapptest can also be used directly from Python.

---

### CI/CD Runner

```python
from fastapptest.cli.ci_runner import run_ci_cd_tests

run_ci_cd_tests(
    project_root="path/to/fastapi_project",
    output_dir="ci_reports",
    auth={"Authorization": "Bearer <token>"},
    fail_fast=True
)
```

---

### Batch Runner

```python
from fastapptest.cli.batch_runner import run_batch_tests

run_batch_tests(
    project_root="path/to/fastapi_project",
    batch_file="batch_payload.json",
    output_file="batch_reports/report.json",
    auth={"Authorization": "Bearer <token>"}
)
```

---

## Authentication Support

fastapptest supports common authentication mechanisms by injecting headers into requests:

* **Bearer Token (JWT)**

  ```json
  {"Authorization": "Bearer <token>"}
  ```

* **API Key**

  ```json
  {"X-API-KEY": "<api_key>"}
  ```

Authentication headers are automatically applied to all test requests.

---

## Reports

### JSON Reports

Each test run generates a structured JSON report containing:

* Endpoint path and HTTP method
* Request payload
* Response status code
* Status code validation result
* Response schema validation result
* Response body
* Error details (if any)

---

### Terminal Summary

A concise terminal summary is printed after execution, showing:

* Total endpoints tested
* Passed tests
* Failed tests
* Validation errors

---

## Examples

The `examples/` directory contains **real FastAPI projects generated using FastSecForge**.
These projects are used as integration-level input fixtures to validate fastapptest against realistic, production-style FastAPI applications.

Refer to `examples/EXAMPLES.md` for full details.

---

## Recommended Workflow

1. Install fastapptest in your project environment
2. Ensure your FastAPI application is runnable
3. Use `manual_test` for exploratory and development testing
4. Use `ci_test` in CI/CD pipelines for full coverage
5. Use `batch_test` for targeted endpoint validation
6. Review JSON reports and fix failing endpoints
7. Integrate into GitHub Actions, GitLab CI, or Jenkins

---

## Requirements

* Python 3.9+
* FastAPI
* Pydantic v2+
* requests

---

## License

This project is licensed under the MIT License.

---

## Status

fastapptest is designed for real-world FastAPI applications and CI/CD automation.
The API and CLI are stable, and the project is actively maintained.



