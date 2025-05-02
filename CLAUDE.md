# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Test/Lint Commands

- Run Django server: `python manage.py runserver`
- Database migrations: `python manage.py migrate`
- Run all tests: `pytest`
- Run single test: `pytest shopping/tests.py::TestClassName::test_specific_function`
- Code formatting: `black .`
- Lint checks: `flake8`
- Import sorting: `isort .`
- Import sample data: `python manage.py import_products`

## Code Style Guidelines

- Follow Django Style Guide: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/
- Use Black for Python code formatting (line length: 88 characters)
- Imports should be sorted with isort: standard libraries, third-party packages, local imports
- JavaScript follows ES6+ standards
- Use Python type hints where applicable
- Error handling: use try/except with specific exception classes
- Naming: Django-style (URLConf, models in singular form)
- Model relationships: use descriptive related_name attributes
- Comment complex logic and business rules
- Keep view logic minimal, use model methods for business logic