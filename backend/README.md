# YAOQI Backend (FastAPI)

> M4 milestone, **Stage 1: Foundation**. Minimal runnable skeleton — `app.main:app` + `/health` + envelope middleware. No DB, no Redis, no OSS, no Azure OpenAI yet (those land in Stage 2–4).
>
> 父文档:[../docs/Backend-Architecture_v0.1.md](../docs/Backend-Architecture_v0.1.md) / [../docs/Backend-Deployment-Guide_v0.1.md](../docs/Backend-Deployment-Guide_v0.1.md) / [../skills/backend-engineer.md](../skills/backend-engineer.md)

---

## Stack

- Python **3.12**
- FastAPI 0.115 / Pydantic 2.9 / pydantic-settings 2.6
- Uvicorn + Gunicorn(`UvicornWorker`)
- structlog(JSON logs)
- pytest 8 / httpx / ruff / mypy --strict
- Package mgmt: **uv** 0.4.30(via conda env)

> Stage 2-4 will add: SQLAlchemy 2.0 / asyncpg / Alembic / pgvector / Redis / Arq / openai / instructor / oss2 / aliyun-python-sdk-* / passlib / pyjwt / testcontainers.

---

## 本地启动

> 项目约定:**conda 管解释器**(参见根目录 `AGENT.md`),**uv 管包**(参见 `skills/backend-engineer.md`)。两者各管各的,不冲突。

```bash
# 1. 建 conda 环境(只装 Python 解释器)
conda create -n yaoqi-backend python=3.12 -y
conda activate yaoqi-backend

# 2. 装 uv,然后用 uv 同步依赖
pip install uv==0.4.30
cd backend
uv sync

# 3. 准备 env
cp .env.example .env
# Stage 1 不需要改任何值,默认 APP_ENV=local 即可跑

# 4. 跑起来
uv run uvicorn app.main:app --reload --port 8000

# 5. 验证
curl -s http://localhost:8000/health | jq
# 期望:{"ok":true,"data":{"status":"ok","version":"0.1.0","checks":{"self":"ok"}},"source":"real"}
```

---

## 测试 / 类型 / lint

```bash
uv run pytest -v                    # 全部测试
uv run ruff check .                 # lint
uv run ruff format --check .        # 格式
uv run mypy --strict app/           # 类型严格
```

CI 顺序与上述一致;任一失败阻塞 merge。

---

## Docker

> Dockerfile 基座固定 `python:3.12-slim-bookworm`;**`<digest>` 占位需在合并前回填**。
>
> 查 digest:`docker buildx imagetools inspect python:3.12-slim-bookworm | grep -m1 -i digest`

```bash
# build
docker build -t yaoqi-backend:dev backend/

# run
docker run --rm -p 8000:8000 --env-file backend/.env yaoqi-backend:dev
curl -s http://localhost:8000/health | jq .data.status   # "ok"
```

`entrypoint.sh` 现支持 `api` / `shell`;Stage 2 加 `migrate`,Stage 4 加 `worker`。

---

## 信封约定

后端响应严格遵循 `web/lib/types/domain.ts` 的 `ApiResponse<T>`:

```jsonc
// 成功
{"ok": true, "data": <T>, "source": "real"}

// 失败
{"ok": false, "error": "<人类可读中文短句>", "source": "real"}
```

- `source` 默认 `real`(真后端真数据)。Stage 1 暂无 mock 切换;Stage 2 起按 `MOCK_*` env 决定。
- 错误 `code`(机器可读)Backend-Architecture §11.1 标 P1 引入,**Stage 1 不实现**。当前只有人类可读 `error` 字符串。
- `X-Request-ID` 在 HTTP header 透传 / 自动生成,**不**进 body(对齐前端 TS 接口形状)。

---

## 目录结构(Stage 1 现状)

```
backend/
├─ pyproject.toml / uv.lock / .python-version
├─ Dockerfile / .dockerignore
├─ scripts/entrypoint.sh
├─ app/
│  ├─ main.py                    # FastAPI 入口 + 中间件挂载
│  ├─ core/
│  │  ├─ config.py               # pydantic-settings Settings
│  │  ├─ logging.py              # structlog 初始化
│  │  └─ exceptions.py           # AppException + handler
│  ├─ schemas/envelope.py        # ApiResponse[T] / 错误信封
│  ├─ middleware/                # request_id / envelope / error_handler
│  ├─ deps/                      # 依赖工厂(Stage 2 起填实)
│  └─ api/v1/health.py           # GET /health
└─ tests/                        # pytest + httpx AsyncClient
```

Stage 2 起会扩 `app/db/`、`app/services/`、`app/integrations/`、`app/workers/`。结构按 [Backend-Architecture §4.1](../docs/Backend-Architecture_v0.1.md) 落。

---

## 红线(scaffolding 阶段已生效)

- ❌ 任何 secret 进 git / 镜像(skills #11)
- ❌ 引入 LangChain / LlamaIndex / DSPy / Celery / RQ / Prisma / NestJS(skills #12)
- ❌ 绕开 `EnvelopeMiddleware` 直接返裸 dict(skills #10)
- ❌ 给 Pydantic Settings 默认值塞真值;真值走 env 注入

完整 13 红线见 [skills/backend-engineer.md](../skills/backend-engineer.md)。

---

## Stage 2-4 待办(本 Stage 不动)

- Stage 2:ORM 13 表 + Alembic 初始迁移 + testcontainers + `/health` 加 DB/Redis 探活
- Stage 3:7 个 tier 报告 schema + 字段裁剪服务
- Stage 4:auth/cases/reports 路由 stub + RBAC + LLMClient Protocol + OSS/OCR/SMS/AOAI client stubs + `tests/test_rbac_redlines.py`
