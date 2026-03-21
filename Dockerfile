# Root Dockerfile for Railway - Backend Service
# This tells Railway to use the backend Dockerfile

FROM python:3.13-slim

WORKDIR /app

# Copy backend code
COPY coredent-api/ .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
