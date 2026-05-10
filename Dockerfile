FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure data directory exists for SQLite DB
RUN mkdir -p /app/data

EXPOSE 8000

# Single worker — SQLite write serialisation; safe for read-heavy DFIR tool
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
