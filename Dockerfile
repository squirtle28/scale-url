FROM python:3.12-slim

WORKDIR /app

# System deps needed to build psycopg's C extension bindings.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .

EXPOSE 8000

# This image is used both for the one-off "migrate" service and for the
# three backend instances (see docker-compose.yml), which override this
# default command to just run uvicorn once migrations have completed.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
