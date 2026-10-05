# Multi-stage production container for JPMC Cross-Channel Credit Card & Fraud Mitigation Agent
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    pip install --no-cache-dir --user -r requirements.txt

# Final Runtime Image
FROM python:3.11-slim

WORKDIR /app

# Copy installed python dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Copy application source code and web assets
COPY jpmc_agent ./jpmc_agent
COPY ui ./ui
COPY web_server.py .
COPY run_adk_tests.py .
COPY tests ./tests

EXPOSE 8080

# Production launch via uvicorn with worker concurrency
CMD ["uvicorn", "web_server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
