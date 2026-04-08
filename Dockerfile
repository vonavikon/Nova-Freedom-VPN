FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot/ ./bot/

# Create directories
RUN mkdir -p /opt/nova-vpn/data /opt/nova-vpn/data/configs /opt/nova-vpn/logs /app/data

# Set environment variables
ENV BOT_TOKEN=${BOT_TOKEN}
ENV ADMIN_IDS=${ADMIN_IDS}
ENV HIDDIFY_API_URL=${HIDDIFY_API_URL}
ENV HIDDIFY_API_KEY=${HIDDIFY_API_KEY}
ENV HIDDIFY_SUBSCRIPTION_BASE=${HIDDIFY_SUBSCRIPTION_BASE}
ENV HIDDIFY_REALITY_DOMAIN=${HIDDIFY_REALITY_DOMAIN}

# Run bot
CMD ["python", "-u", "bot/main.py"]
