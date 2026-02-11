# Use a lightweight Python image
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
# We list them directly here to avoid needing a separate requirements.txt file for simple builds
RUN pip install --no-cache-dir redis bcrypt cryptography

# Copy the server code
COPY server.py .

# Copy the certificates (These must be generated before building!)
COPY server.crt .
COPY server.key .

# Default command (can be overridden by docker-compose)
CMD ["python", "server.py"]