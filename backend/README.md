# YAOQI Backend (FastAPI)

> M4 milestone, **Stage 2: Persistence** ✅. Stage 1 Foundation + 13 SQLAlchemy 2.0 async ORMs + Alembic 初始迁移(扩展 / CHECK / 部分索引 / 触发器 / pgvector)+ testcontainers fixture + `/health` 加 `checks.db`。
>
> 还**没**有的:DAO/Service/Repository、路由 stub、RBAC、LLMClient、OSS/OCR/SMS clients、Seed —— 这些是 Stage 3-4。
>
> 父文档:[../docs/Backend-Architecture_v0.1.md](../docs/Backend-Architecture_v0.1.md) / [../docs/Backend-Database-Schema_v0.1.md](../docs/Backend-Database-Schema_v0.1.md) / [../docs/Backend-Deployment-Guide_v0.1.md](../docs/Backend-Deployment-Guide_v0.1.md) / [../skills/backend-engineer.md](../skills/backend-engineer.md)

---

## Stack

- Python **3.12**
- FastAPI 0.115 / Pydantic 2.9 / pydantic-settings 2.6
- **SQLAlchemy 2.0(async)** + asyncpg + Alembic + pgvector(Stage 2)
- Uvicorn + Gunicorn(`UvicornWorker`)
- structlog(JSON logs)
- pytest 8 / httpx / **testcontainers**(真 PG)/ ruff / mypy --strict
- Package mgmt: **uv** 0.4.30(via conda env)

> Stage 3-4 will add: Redis / Arq / openai / instructor / oss2 / aliyun-python-sdk-* / passlib / pyjwt。

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

# 3. 起本地 Postgres(pgvector pre-installed,与生产 RDS PG16 + pgvector 对齐)
docker run -d --name yaoqi-pg-dev \
  -e POSTGRES_USER=yq_app -e POSTGRES_PASSWORD=CHANGEME -e POSTGRES_DB=yaoqi \
  -p 5432:5432 pgvector/pgvector:pg16

# 4. 准备 env(默认 DATABASE_URL 已指向上面的本地 PG)
cp .env.example .env

# 5. 跑 Alembic 升级到 head
uv run alembic upgrade head
# 期望:13 表 + 3 扩展 + 7 触发器 + 9 部分索引/GIN/ivfflat 落盘
# 反向验证(可选):uv run alembic downgrade base && uv run alembic upgrade head
# 检测 ORM ↔ DDL 漂移:uv run alembic check  (exit 0 = 无 pending diff)

# 6. 跑起来
uv run uvicorn app.main:app --reload --port 8000

# 7. 验证
curl -s http://localhost:8000/health | jq
# 期望:{"ok":true,"data":{"status":"ok","checks":{"self":"ok","db":"ok"}},"source":"real"}

# 8. 停 PG 验证降级(可选)
docker stop yaoqi-pg-dev && curl -s http://localhost:8000/health | jq
# 期望:HTTP 仍 200,data.status="degraded",checks.db="unavailable"(D5)
```

---

## 测试 / 类型 / lint

> **⚠️ Stage 2 起,跑 `pytest` 需要本机 Docker daemon(testcontainers 起 pgvector container)。**
> 首次会拉 `pgvector/pgvector:pg16` 镜像(1-2 min);后续命中 layer cache 秒级起。
> CI(GitHub Actions)在 PG 上 cache image layer 即可。

```bash
uv run pytest -v                    # 全部测试(testcontainers 自起 PG,无需手动 docker run)
uv run ruff check .                 # lint
uv run ruff format --check .        # 格式
uv run mypy --strict app/           # 类型严格(不含 alembic/versions/)
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

`entrypoint.sh` 现支持 `api` / `migrate` / `shell`;Stage 4 会加 `worker`。
部署流水线建议:`docker run --rm yaoqi-backend migrate` → `docker run -d yaoqi-backend api`(先迁后启)。

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

## 目录结构(Stage 2 现状)

```
backend/
├─ pyproject.toml / uv.lock / .python-version
├─ Dockerfile / .dockerignore
├─ alembic.ini
├─ alembic/
│  ├─ env.py                       # async pattern,target_metadata=Base.metadata
│  ├─ script.py.mako
│  └─ versions/0001_init.py        # 13 表 + 扩展 + CHECK + 索引 + 触发器 + pgvector
├─ scripts/entrypoint.sh           # api | migrate | shell
├─ app/
│  ├─ main.py                      # FastAPI 入口 + 中间件挂载
│  ├─ core/
│  │  ├─ config.py                 # Settings(含 db_pool / health_db_timeout)
│  │  ├─ logging.py                # structlog 初始化
│  │  └─ exceptions.py             # AppException + handler
│  ├─ schemas/envelope.py          # ApiResponse[T] / 错误信封
│  ├─ middleware/                  # request_id / envelope / error_handler
│  ├─ db/
│  │  ├─ base.py                   # DeclarativeBase + IdMixin + TimestampMixin + MockableMixin
│  │  ├─ session.py                # create_async_engine + async_sessionmaker
│  │  └─ models/                   # 13 ORM 一表一文件
│  ├─ deps/db.py                   # get_db() → AsyncSession
│  └─ api/v1/health.py             # GET /health(self + db)
└─ tests/                          # pytest + httpx + testcontainers
```

Stage 3 起会扩 `app/services/`、`app/integrations/`、`app/workers/`。结构按 [Backend-Architecture §4.1](../docs/Backend-Architecture_v0.1.md) 落。

---

## 红线(scaffolding 阶段已生效)

- ❌ 任何 secret 进 git / 镜像(skills #11)
- ❌ 引入 LangChain / LlamaIndex / DSPy / Celery / RQ / Prisma / NestJS(skills #12)
- ❌ 绕开 `EnvelopeMiddleware` 直接返裸 dict(skills #10)
- ❌ 给 Pydantic Settings 默认值塞真值;真值走 env 注入

完整 13 红线见 [skills/backend-engineer.md](../skills/backend-engineer.md)。

---

## Stage 3-4 待办(本 Stage 不动)

- Stage 3:7 个 tier 报告 Pydantic schema + `crop_report_for_user(tier)` 服务端裁剪
- Stage 4:auth/cases/reports 路由 stub + RBAC + LLMClient Protocol + OSS/OCR/SMS/AOAI client stubs + Seed(super_admin / 字典)+ `/health` 扩 `checks.redis/oss/aoai` + `tests/test_rbac_redlines.py`
