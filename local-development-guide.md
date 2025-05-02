# ShopSmart Local Development Guide

This guide will help you set up and run ShopSmart in your local development environment using Docker and PostgreSQL for development-production parity.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- Python 3.8+ (for non-Docker development)
- Git

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ShopSmart
```

### 2. Environment Setup

Create a `.env` file in the root directory with the following variables:

```
# Database Configuration
DB_NAME=shopsmart
DB_USER=shopsmart_user
DB_PASSWORD=your_secure_password
DB_HOST=db
DB_PORT=5432

# Django Settings
DEBUG=True
SECRET_KEY=your_development_secret_key
ALLOWED_HOSTS=localhost,127.0.0.1

# API Keys
OPEN_FOOD_FACTS_USER_AGENT=ShopSmart/1.0 (your@email.com)
```

### 3. Running with Docker (Recommended)

This method provides the closest environment to production:

```bash
# Start PostgreSQL and pgAdmin
docker-compose -f docker-compose.dev.yml up -d

# Apply migrations
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate

# Create a superuser
docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser

# Populate products database (optional)
docker-compose -f docker-compose.dev.yml exec web python manage.py populate_products --limit 100
```

Access the application:
- ShopSmart: http://localhost:8000
- pgAdmin: http://localhost:5050 (login with credentials from docker-compose.dev.yml)

### 4. Manual Setup (Without Docker)

If you prefer not to use Docker:

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up a local PostgreSQL instance and update your `.env` file with the appropriate connection details.

4. Apply migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## Development Workflow

### Database Migrations

After changing models:

```bash
# Generate migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

With Docker:
```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py makemigrations
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
```

### Testing

Run tests:

```bash
python manage.py test
```

With Docker:
```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py test
```

### Populating the Database

To populate the product database with data from Open Food Facts:

```bash
python manage.py populate_products --limit 100 --country us --categories "breakfast cereals,dairy,snacks"
```

With Docker:
```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py populate_products --limit 100 --country us --categories "breakfast cereals,dairy,snacks"
```

### Working with pgAdmin

1. Access pgAdmin at http://localhost:5050
2. Login using the credentials from docker-compose.dev.yml
3. Add a new server with:
   - Host: db
   - Port: 5432
   - Database: shopsmart
   - Username: shopsmart_user
   - Password: (from .env file)

## Debugging Tips

### Checking Logs

View logs for the application:
```bash
docker-compose -f docker-compose.dev.yml logs -f web
```

View database logs:
```bash
docker-compose -f docker-compose.dev.yml logs -f db
```

### Resetting the Database

To completely reset your development database:

```bash
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
```

### Accessing the Docker Shell

For debugging within containers:

```bash
docker-compose -f docker-compose.dev.yml exec web bash
```

## Developing Offline Features

To test offline functionality:
1. Access the application in Chrome
2. Open Developer Tools (F12)
3. Go to the Network tab
4. Enable "Offline" mode
5. Test the application's offline capabilities

Remember that the Service Worker requires HTTPS in production, but works over HTTP in development.

## Common Issues and Solutions

1. **Database connection errors**:
   - Ensure your PostgreSQL service is running
   - Check that environment variables match your database configuration
   - Verify network settings if using Docker

2. **Static files not loading**:
   - Run `python manage.py collectstatic`
   - Check STATIC_URL and STATIC_ROOT in settings.py

3. **API rate limiting**:
   - Open Food Facts API has rate limits; use smaller batch sizes when populating products

4. **Docker disk space issues**:
   - Clear unused Docker resources: `docker system prune -a`