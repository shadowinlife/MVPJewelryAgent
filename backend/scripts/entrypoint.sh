#!/usr/bin/env bash
# YAOQI Backend container entrypoint.
# Stage 1: api | shell. Stage 2 adds `migrate`. Stage 4 adds `worker`.

set -euo pipefail

case "${1:-api}" in
  api)
    exec gunicorn app.main:app \
      --workers 4 \
      --worker-class uvicorn.workers.UvicornWorker \
      --bind 0.0.0.0:8000 \
      --timeout 60 \
      --access-logfile -
    ;;
  shell)
    exec python
    ;;
  *)
    exec "$@"
    ;;
esac
