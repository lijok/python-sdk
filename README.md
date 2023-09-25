# python-sdk
Software Development Kit for Python, otherwise known as a Microservice Chassis, which handles cross-cutting concerns such as:
- Logging
- Metrics
- Tracing
- Configuration
- Secrets
- Versioning
- Health checks

## WARNING
This library is still in development and does not have stable interfaces. While it is in use by some internal projects, it is not yet recommended for any productions workloads.

## Requirements
Python 3.10+

## Installation
```console
pip install pythonsdk

# If using AWS functionality
pip install pythonsdk[aws]

# If using CLI functionality
pip install pythonsdk[cli]

# If using `testing` package
pip install pythonsdk[testing]
```

## Packages
Below is an abstract of the functionality provided by this library. See [`docs`](https://github.com/lijok/python-sdk/blob/main/src/python_sdk/docs) for more information.

### [`bin`](https://github.com/lijok/python-sdk/blob/main/src/python_sdk/bin/__init__.py)
The `bin` package provides utilities for invoking processes while streaming, capturing and manipulating their output.

### [`config`](https://github.com/lijok/python-sdk/blob/main/src/python_sdk/config/__init__.py)
The `config` package provides a declarative mechanism for defining your application config, with support for multiple configuration sources (environment variables, remote HTTP endpoints, S3 objects, etc.) validation, secrets injection, hot-reloading, documentation, etc.

### [`encoding`](https://github.com/lijok/python-sdk/blob/main/src/python_sdk/encoding/__init__.py)
The `encoding` package provides some encoding utils commonly used when authoring networked APIs.

### [`locks`](https://github.com/lijok/python-sdk/blob/main/src/python_sdk/locks/__init__.py)
The `locks` package contains a distributed locking mechanism backed by multiple different providers.

### [`log`](https://github.com/lijok/python-sdk/blob/main/src/python_sdk/log/__init__.py)
The `log` package contains an externally configurable logging interface which supports structured logging and hot reloading.

### [`secrets`](https://github.com/lijok/python-sdk/blob/main/src/python_sdk/secrets/__init__.py)
The `secrets` package provides a simple interface for reading in secrets stored in secrets stores such as AWS Secrets Manager.

### [`service`](https://github.com/lijok/python-sdk/blob/main/src/python_sdk/service/__init__.py)
The `service` package provides a uvicorn-like service component for running non-webapp services (workers).

### [`testing`](https://github.com/lijok/python-sdk/blob/main/src/python_sdk/testing/__init__.py)
The `testing` package provides a highly opinionated acceptance test suite for enforcing code quality. 

### [`versioning`](https://github.com/lijok/python-sdk/blob/main/src/python_sdk/versioning/__init__.py)
The `versioning` package provides language-agnostic application versioning strategies.

## Interfaces
### CLI
The cli `python-sdk` provides dev-time utilities such as a highly opinionated formatter (`python-sdk fmt`).
