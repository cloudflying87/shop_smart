# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Test/Lint Commands

### Standard Development
- Run Django server: `python manage.py runserver`
- Database migrations: `python manage.py migrate`
- Make migrations: `python manage.py makemigrations`
- Run all tests: `python manage.py test`
- Run specific test module: `python manage.py test shopping.tests.test_models`
- Run specific test class: `python manage.py test shopping.tests.test_models.FamilyModelTests`
- Run specific test method: `python manage.py test shopping.tests.test_models.FamilyModelTests.test_family_creation`
- Code formatting: `black .`
- Lint checks: `flake8`
- Import sorting: `isort .`
- Populate product database: `python manage.py populate_products --limit 100`
- Populate store database: `python manage.py populate_stores`
  - List available stores: `python manage.py populate_stores --list`
  - Add specific stores: `python manage.py populate_stores --stores "Walmart" "Target"`
  - Skip logo downloads: `python manage.py populate_stores --nologos`
  - Associate with specific family: `python manage.py populate_stores --family 1`
- Add basic household items: `python manage.py add_basic_items`

### Docker Development
- Start development services: `docker-compose -f docker-compose.dev.yml up -d`
- Run migrations in container: `docker-compose -f docker-compose.dev.yml exec web python manage.py migrate`
- Run tests in container: `docker-compose -f docker-compose.dev.yml exec web python manage.py test`
- Create superuser in container: `docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser`
- View logs: `docker-compose -f docker-compose.dev.yml logs -f web`
- Populate database in container:
  - Products: `docker-compose -f docker-compose.dev.yml exec web python manage.py populate_products --limit 100`
  - Stores: `docker-compose -f docker-compose.dev.yml exec web python manage.py populate_stores`
    - List available stores: `docker-compose -f docker-compose.dev.yml exec web python manage.py populate_stores --list`
    - Add specific stores: `docker-compose -f docker-compose.dev.yml exec web python manage.py populate_stores --stores "Walmart" "Target"`
    - Skip logo downloads: `docker-compose -f docker-compose.dev.yml exec web python manage.py populate_stores --nologos`
  - Basic Items: `docker-compose -f docker-compose.dev.yml exec web python manage.py add_basic_items`

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