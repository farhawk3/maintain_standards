# Dockerfile for the Standards Library Application
# Simplified single-stage build for debugging.

# Use an official Python 3.9 slim image as the base.
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container.
WORKDIR /app

# Copy requirements and install dependencies
# Copy requirements first to leverage cache
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application code (Backend and Frontend)
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY entrypoint.sh /app/

# Copy the data directory
COPY standards_library/ /app/standards_library/

# Set the absolute path to the data directory inside the container.
# We point to /tmp/standards_library because Cloud Run filesystem is read-only
ENV DATA_PATH=/tmp/standards_library

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Tell Cloud Run that the container will listen on port 8080.
EXPOSE 8080

# Define the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Run Gunicorn from the backend directory
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--chdir", "backend", "app:app"]
