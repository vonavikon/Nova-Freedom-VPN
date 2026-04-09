FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot/ ./bot/

# Create directories
RUN mkdir -p /opt/nova-vpn/data /opt/nova-vpn/data/configs /opt/nova-vpn/logs /app/data

# All config comes from .env via docker-compose env_file

# Run bot
CMD ["python", "-u", "bot/main.py"]
