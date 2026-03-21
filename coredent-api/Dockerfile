FROM python:3.12-slim AS builder
WORKDIR /app

# Install build dependencies for C extensions (asyncpg, pydantic-core, hiredis)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    make \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Optimize layer caching: Copy and install requirements separately
# When building from root, requirements.txt is in coredent-api/
COPY coredent-api/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final stage
FROM python:3.12-slim
WORKDIR /app

# Install runtime dependencies (e.g., curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code (from coredent-api directory)
COPY coredent-api/ .

# Ensure alembic.ini is in the correct location
RUN cp /app/alembic.ini /app/alembic.ini 2>/dev/null || true

# Create non-root user for security (HIPAA Best Practice)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check using curl (HIPAA: Monitoring uptime)
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application (migrations should be run separately via Railway job or CLI)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
