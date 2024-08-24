# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.11.4
FROM python:${PYTHON_VERSION}-slim as base

# Optimize Python behavior in Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /

# Create a non-privileged user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/appuser" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser
# Create the home directory and give ownership to appuser
RUN mkdir -p /home/appuser && chown appuser:appuser /home/appuser

# Install dependencies with cache optimizations
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=celery_worker/requirements.txt,target=requirements.txt \
    python -m pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY ./myapp /myapp

# Switch to non-privileged user
USER appuser

CMD ["celery", "-A", "myapp.celery_app", "worker", "--loglevel=info"]
