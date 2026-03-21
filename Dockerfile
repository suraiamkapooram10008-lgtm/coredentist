# Backend Dockerfile for Railway
FROM python:3.13-slim

WORKDIR /app

# Copy only backend requirements first (for better caching)
COPY coredent-api/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY coredent-api/ .

# Expose port
EXPOSE $PORT

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
