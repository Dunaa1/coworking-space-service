# Use the slim Python 3.10 image to keep the final image lightweight
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required by psycopg2
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Upgrade pip toolchain then install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5153

CMD ["python", "app.py"]
