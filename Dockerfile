# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev gcc python3-dev musl-dev \
    nginx \
    redis-server

# Install Python dependencies
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files
COPY . /usr/src/app/

# Copy Nginx configuration
COPY ./nginx/nginx.conf /etc/nginx/nginx.conf

# Prepare nginx runtime dirs (some slim images may not have these)
RUN mkdir -p /var/log/nginx /var/run /var/cache/nginx

# Collect static files (ensure settings are configured for STATIC_ROOT)
RUN python manage.py collectstatic --noinput || true

# Expose the ports for Redis and Django app
EXPOSE 6379 8000

# Start Redis (daemon) and run Gunicorn in foreground on $PORT (Render)
CMD redis-server --daemonize yes && \
    gunicorn veyu.asgi:application --bind 0.0.0.0:${PORT:-8000}
