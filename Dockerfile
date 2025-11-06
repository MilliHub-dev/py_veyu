# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /usr/src/app

# Create logs directory with proper permissions
RUN mkdir -p /usr/src/app/logs && \
    chmod -R 777 /usr/src/app/logs

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

# Start Redis (daemon) and run Daphne ASGI server on $PORT (Render)
CMD redis-server --daemonize yes && \
    daphne -b 0.0.0.0 -p ${PORT:-8000} veyu.asgi:application
