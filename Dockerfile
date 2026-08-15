# Use official lightweight Python base image
FROM python:3.11-slim

# Set environment variables for security and non-interactive builds
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create low-privilege non-root user
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -s /bin/sh -m appuser

WORKDIR /app

# Install dependencies first for efficient layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Change ownership of application files to non-root user
RUN chown -R appuser:appuser /app

# Switch to low-privilege user (Runtime Lockdown)
USER appuser

# Entry point in headless background mode for container environments
CMD ["python", "main.py", "--headless"]
