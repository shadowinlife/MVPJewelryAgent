#!/usr/bin/env bash
# YAOQI Backend container entrypoint.
# Stage 1: api | shell. Stage 2 adds `migrate`. Stage 4 will add `worker`.

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
  migrate)
    # Stage 2: 跑 Alembic 升级到 head。
    # 用法:`docker run --rm yaoqi-backend migrate`(部署流水线中先 migrate 再起 api)
    exec uv run alembic upgrade head
    ;;
  shell)
    exec python
    ;;
  *)
    exec "$@"
    ;;
esac
