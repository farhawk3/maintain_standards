# Dockerfile for the Moral Standards Manager Application

# --- Stage 1: Build the Python Backend ---
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Copy only the requirements file to leverage layer caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application code
COPY backend/ .

# --- Stage 2: Use a production-ready web server (Caddy) to serve both frontend and backend ---
FROM caddy:2-alpine

# Copy the built backend from the previous stage
COPY --from=0 /app /app

# Copy the frontend files
COPY frontend/ /srv/

# Copy the Caddyfile configuration
COPY Caddyfile /etc/caddy/Caddyfile

# Expose the port Caddy listens on (Google Cloud Run uses 8080 by default)
EXPOSE 8080
