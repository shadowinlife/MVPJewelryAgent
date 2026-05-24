# YAOQI Backend — Dockerfile
#
# Stage 1 base. Pin to digest before merging:
#   docker buildx imagetools inspect python:3.12-slim-bookworm | grep -m1 -i digest
# Replace the FROM line with `python:3.12-slim-bookworm@sha256:<digest>`.
# Security-Checklist H-03 requires fixed digest; `:latest` is forbidden.
FROM python:3.12-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl tini \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.4.30

# Non-root user (Security-Checklist I-10).
RUN useradd -m -u 1000 appuser
WORKDIR /app

# Dependency layer — only re-runs when pyproject.toml / uv.lock change.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

# Code layer.
COPY app/ ./app/
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && chown -R appuser:appuser /app

USER appuser
ENV PATH="/app/.venv/bin:${PATH}"
EXPOSE 8000

ENTRYPOINT ["tini", "--", "/usr/local/bin/entrypoint.sh"]
CMD ["api"]
