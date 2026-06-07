# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final minimal runtime container
FROM python:3.11-slim AS runner

WORKDIR /app

# Create a non-privileged user to run the app for security
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -s /sbin/nologin -m appuser

# Copy installed dependencies from builder
COPY --from=builder /usr/local /usr/local
COPY --chown=appuser:appuser . .

ENV PORT=5000
ENV PYTHONUNBUFFERED=1

USER appuser

EXPOSE 5000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT --workers 2 app:app"]
