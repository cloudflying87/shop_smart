# ShopSmart

ShopSmart is a Progressive Web Application (PWA) designed to simplify grocery shopping. It allows users to create, manage, and share shopping lists with family members, track prices, and receive personalized recommendations based on shopping history.

![ShopSmart Screenshot](static/img/screenshot.png)

## Key Features

- **Family Sharing**: Share shopping lists with family members in real-time
- **Multiple Store Support**: Organize items by store with store-specific locations
- **Offline Functionality**: Create and update lists even without an internet connection
- **Price Tracking**: Monitor and compare prices across different stores
- **Personalized Recommendations**: Get suggestions based on your shopping history
- **Dark Mode**: Comfortable viewing experience in any lighting
- **Responsive Design**: Optimized for mobile devices

## Tech Stack

- **Backend**: Django
- **Frontend**: HTML, CSS, JavaScript
- **Database**: PostgreSQL
- **Deployment**: Docker with Cloudflared
- **External API**: Open Food Facts for product database

## Installation

### Prerequisites

- Python 3.9+
- Node.js 14+
- PostgreSQL
- Docker (optional for production deployment)

### Development Setup

#### Method 1: Using Docker (Recommended)

This method provides the closest environment to production:

1. Clone the repository
```bash
git clone https://github.com/yourusername/shopsmart.git
cd shopsmart
```

2. Set up environment variables
```bash
cp .env.example .env
# Edit .env file with your configuration
```

3. Start PostgreSQL and the application with Docker Compose
```bash
docker-compose -f docker-compose.dev.yml up -d
```

4. Apply migrations
```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
```

5. Create a superuser
```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

6. Populate product database (optional)
```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py populate_products --limit 100
```

The application will be available at http://localhost:8000
pgAdmin will be available at http://localhost:5050

#### Method 2: Manual Setup

1. Clone the repository
```bash
git clone https://github.com/yourusername/shopsmart.git
cd shopsmart
```

2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
```bash
cp .env.example .env
# Edit .env file with your configuration
```

5. Run migrations
```bash
python manage.py migrate
```

6. Populate product database (optional)
```bash
python manage.py populate_products --limit 100
```

7. Run the development server
```bash
python manage.py runserver
```

The application will be available at http://localhost:8000

For more detailed instructions, see [Local Development Guide](local-development-guide.md)

## Production Deployment

### Using Docker

1. Build the Docker image
```bash
docker-compose build
```

2. Start the containers
```bash
docker-compose up -d
```

3. Run migrations
```bash
docker-compose exec web python manage.py migrate
```

4. Create a superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### Manual Deployment

For a production environment, we recommend:

1. Using Gunicorn as the WSGI server
2. Nginx as a reverse proxy
3. PostgreSQL for the database
4. Redis for caching (optional)

Refer to the [Architecture Guide](docs/architecture-guide.md) for detailed deployment instructions.

## Project Structure

```
ShopSmart/
├── manage.py
├── shopsmart/                # Project directory
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── groceries/                # Main app directory
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views/                # Views organized by feature
│   ├── forms.py
│   ├── urls.py
│   ├── recommender.py        # Recommendation system
│   ├── utils.py              # Utility functions
│   ├── templates/
│   └── static/
├── static/                   # Project-wide static files
│   ├── js/
│   │   ├── app.js
│   │   ├── modal-handler.js
│   │   ├── theme-manager.js
│   │   ├── mobile-nav.js
│   │   ├── error-handler.js
│   │   ├── ajax-util.js
│   │   ├── form-validator.js
│   │   └── service-worker.js
│   ├── css/
│   │   ├── base.css
│   │   └── mobile.css
│   ├── manifest.json
│   └── icons/
├── templates/                # Project-wide templates
│   ├── base.html
│   ├── registration/
│   └── 404.html
└── Dockerfile
```

## Offline Support

ShopSmart uses service workers to provide offline functionality. The service worker caches static assets and API responses to ensure the application remains functional even without an internet connection.

Key offline features include:
- Viewing existing shopping lists
- Adding items to shopping lists
- Checking off items
- Creating new lists (with sync when online)

## Error Handling and User Feedback

ShopSmart implements robust error handling and user feedback mechanisms to provide a smooth experience:

- Visual feedback for all user actions
- Informative error messages
- Optimistic UI updates with fallbacks
- Form validation with clear indications
- Offline mode indicators

## Progressive Web App Features

To install ShopSmart as a PWA on your device:

### On Android
1. Open the website in Chrome
2. Tap the menu button (three dots)
3. Select "Add to Home Screen"

### On iOS
1. Open the website in Safari
2. Tap the Share button
3. Select "Add to Home Screen"

## Development Guidelines

- Follow the [Django Style Guide](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/)
- Use JavaScript ES6+ features
- Write tests for new features
- Document code changes

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Django](https://www.djangoproject.com/)
- [WhiteNoise](http://whitenoise.evans.io/) for static file serving
- [Open Food Facts](https://world.openfoodfacts.org/) for product datawhy d