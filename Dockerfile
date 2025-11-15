# Use an official Python runtime as a parent image
# This provides a lean, secure base with Python 3.9 pre-installed.
FROM python:3.9-slim

# Set environment variables to improve container performance and security
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk.
# PYTHONUNBUFFERED: Ensures Python output is sent straight to logs, crucial for debugging.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a non-root user and group for security.
# Running as a non-root user is a critical security best practice.
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy only the requirements file first to leverage Docker's layer caching.
# If requirements.txt doesn't change, this step won't be re-run on future builds.
COPY requirements.txt .

# Upgrade pip and install the Python packages.
# --no-cache-dir reduces the final image size.
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Set the working directory for the application inside the user's home directory.
WORKDIR /home/appuser/app

# Copy the rest of the application's code into the working directory.
# --chown sets the owner of the copied files to our non-root user.
COPY --chown=appuser:appgroup . .

# Explicitly grant execute permissions to the entrypoint script. This is crucial
# because file permissions are not always preserved across file systems (e.g., from Windows to Linux).
RUN chmod +x entrypoint.sh

# Switch from the root user to our newly created non-root user.
USER appuser

# Expose the port that Streamlit runs on. This is metadata for the container.
# Cloud Run will automatically provide the correct PORT environment variable and map it.
EXPOSE 8501

# Set the entrypoint script to run when the container starts.
ENTRYPOINT ["./entrypoint.sh"]
