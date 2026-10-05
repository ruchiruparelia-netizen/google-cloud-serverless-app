import os

# Gunicorn configuration
bind = "0.0.0.0:" + os.environ.get("PORT", "8080")
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "60"))
loglevel = "info"
