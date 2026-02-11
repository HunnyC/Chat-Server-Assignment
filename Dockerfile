
FROM python:3.9-slim

WORKDIR /app

# Install dependencies

RUN pip install --no-cache-dir redis bcrypt cryptography

# Copy the server code
COPY server.py .

# Copy the certificates 
COPY server.crt .
COPY server.key .

# Default command 
CMD ["python", "server.py"]