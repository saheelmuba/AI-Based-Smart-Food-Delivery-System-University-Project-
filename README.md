# QuickBite Food Delivery

A food delivery website built with Flask. Browse the menu, add items to your cart, place delivery orders, track orders, and chat with an AI assistant.

## Features

- Food menu with categories (pizza, burgers, pasta, drinks, desserts)
- Shopping cart with local storage
- Delivery checkout and order tracking
- Admin dashboard and analytics
- AI food delivery assistant
- Docker-ready Flask backend

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```
3. Run the application:
   ```bash
   python app.py
   ```
   On Windows you can also double-click `run.bat`.

   The browser should open automatically at http://127.0.0.1:5000/

## Pages

- `/` Home
- `/menu` Food menu
- `/cart` Cart and checkout
- `/orders` Order tracking
- `/chatbot` AI assistant
- `/dashboard` Admin dashboard
- `/analytics` Delivery analytics

## Docker Deployment

Build the image:
```bash
docker build -t medical-management-system .
```

Run with Docker Compose:
```bash
docker compose up --build
```

## Production

Use `docker-compose.yml`, `nginx.conf`, and `gunicorn.conf.py` to deploy in production with Nginx as a reverse proxy.

## Testing

Run unit tests with pytest:
```bash
pytest
```
