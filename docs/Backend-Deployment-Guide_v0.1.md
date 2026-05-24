# 曜齐 YAOQI — Backend Deployment Guide v0.1

> M4 部署与运维指南。把 [Backend-Architecture §13 部署](./Backend-Architecture_v0.1.md) + [§9.7 跨云出口](./Backend-Architecture_v0.1.md) + [§16.1 跨云速记](./Backend-Architecture_v0.1.md) 扩展为**可逐步执行**的部署手册。
>
> 父文档:[Backend-Architecture_v0.1.md](./Backend-Architecture_v0.1.md) / [Backend-Database-Schema_v0.1.md](./Backend-Database-Schema_v0.1.md) / [Backend-Security-Checklist_v0.1.md](./Backend-Security-Checklist_v0.1.md)
> 兄弟:[skills/backend-engineer.md](../skills/backend-engineer.md) / [skills/ai-integration-engineer.md](../skills/ai-integration-engineer.md)
> 起始:2026-05-23

---

## 0. 文档定位

| 在哪 | 内容 |
|---|---|
| Backend-Architecture §13 | 部署原则(ECS+RDS+Redis、Dockerfile 示意、CI/CD 概念) |
| Backend-Architecture §9.7 / §16.1 | 跨云出口与拓扑 |
| Backend-Security-Checklist §3.F / §3.I | Secret / 网络 / TLS 红线 |
| **本文档** | **可逐步执行**的:阿里云资源清单 / KMS 注入 / ICP 备案 / ACR 镜像流程 / 滚动发版 / 监控告警 / 回滚剧本 / 上线 checklist |

**仲裁顺序**:本文 ≻ Backend-Architecture §13 / §9.7 / §16.1。
**用法**:M4 实施开工后,部署侧按本文从 §4(物料)→ §15(上线 checklist)逐节执行。Security 红线由 [Backend-Security-Checklist](./Backend-Security-Checklist_v0.1.md) 同步核对。

---

## 1. 环境拓扑

### 1.1 三环境矩阵

| 环境 | 用途 | 域名 | 资源规格 | 数据 |
|---|---|---|---|---|
| **local** | 工程师本地开发 | `localhost:8000` | Docker Compose(pg + redis + minio + 应用) | `is_mock=true` 种子数据 |
| **staging** | 内测 / 回归 | `staging.yaoqi.<host>` | 阿里云 ECS 单台 + RDS 入门版 + Tair 入门版 | 真数据 + mock 标识混合 |
| **production** | 正式公测 | `api.yaoqi.<host>` | ECS 2 台 + SLB + RDS 高可用 + Tair 高可用 | 真数据,`is_mock=false` 默认 |

**禁止**:本地连生产 DB / 用生产 OSS 桶 / 用生产 Azure key。

### 1.2 跨云物理拓扑

```text
┌─────────────── 阿里云(华东 / 杭州 或 张家口)───────────────┐
│                                                              │
│  ┌──────────┐   ┌──────────────────────────────────────────┐ │
│  │  域名 +  │──▶│  SLB(7层 HTTPS) + WAF                  │ │
│  │  ICP备案 │   └──────────┬───────────────────────────────┘ │
│  └──────────┘              │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────┐                │
│  │  ECS-API ×2(gunicorn + uvicorn)         │                │
│  │  ECS-Worker ×1(arq)                      │                │
│  └────┬───────────────┬──────────────┬──────┘                │
│       │               │              │                       │
│       ▼               ▼              ▼                       │
│  ┌────────┐      ┌──────────┐   ┌──────────┐                │
│  │  RDS   │      │  Tair    │   │  OSS     │                │
│  │  PG16  │      │ (Redis7) │   │ (private)│                │
│  │+pgvector│      └──────────┘   └──────────┘                │
│  └────────┘                                                  │
│                                                              │
│  ┌────────┐   ┌────────┐   ┌────────┐                       │
│  │ KMS    │   │  OCR   │   │  SMS   │                       │
│  └────────┘   └────────┘   └────────┘                       │
│                                                              │
└──────────────────────────────┬───────────────────────────────┘
                               │ 公网 HTTPS / timeout=60s
                               ▼
            ┌──────────────────────────────────────┐
            │  Azure OpenAI Service @ HongKong     │
            │  - aoai-private-report (微调)         │
            │  - aoai-deployment-ocr-correct       │
            │  - aoai-deployment-image-summary     │
            │  - aoai-text-embedding-3-small       │
            └──────────────────────────────────────┘
```

排除项(2026-05-22 拍板,**不要回推**):
- ❌ API Gateway / VPN 专线(M4 不引入)
- ❌ k8s / ACK(2 台 ECS + docker compose 足够 MVP)
- ❌ 自建 LB(用阿里云 SLB)
- ❌ 把后端搬到 Azure / OpenAI 平台直连

---

## 2. 阿里云资源清单

> 所有资源**必须**归属"项目方主账号";工程师只发子账号(RAM),最小权限。

### 2.1 计算

| 资源 | 规格 | 数量 | 备注 |
|---|---|---|---|
| ECS-API | `ecs.c7.large`(2 vCPU / 4G) | 2 | 跑 gunicorn,SLB 后挂 |
| ECS-Worker | `ecs.c7.large`(2 vCPU / 4G) | 1 | 跑 arq,M4 单台够 |
| ECS-Jump | `ecs.s6-c1m1.small`(1 vCPU / 1G) | 1 | 跳板机,SSH 只放它的公网 IP |

操作系统:**Anolis OS 23 LTS** 或 **Ubuntu 22.04 LTS**(选熟悉的);所有 ECS 加同一 VPC + 同一 vSwitch。

### 2.2 网络

| 资源 | 配置 |
|---|---|
| VPC | `10.0.0.0/16`,1 个可用区(MVP 不跨区) |
| vSwitch | `10.0.1.0/24`(应用) + `10.0.2.0/24`(数据,RDS/Tair 落这) |
| SLB | 7 层 HTTPS;监听 443 → ECS-API:8000;监听 80 → 301 重定向 443 |
| WAF | 开启 OWASP 规则集(参考 [Security-Checklist I-06](./Backend-Security-Checklist_v0.1.md)) |
| 安全组 sg-api | 入:80 / 443(SLB 内网);出:443(任何,允许 Azure) |
| 安全组 sg-worker | 入:无;出:443 + RDS 端口 + Redis 端口 |
| 安全组 sg-data | 入:仅 sg-api + sg-worker;出:无 |
| 安全组 sg-jump | 入:22(白名单工程师公网 IP);出:22(到 sg-api / sg-worker) |

### 2.3 数据

| 资源 | 规格 | 备注 |
|---|---|---|
| **RDS PostgreSQL 16** | `pg.n2.medium.2c`(2 vCPU / 4G / 100G SSD) | 主从高可用(生产);staging 单实例 |
| RDS 账号 | `yq_app`(只 CRUD) + `yq_migrate`(DDL,部署时用) | 不开公网,只 vSwitch 内网 |
| pgvector 扩展 | `CREATE EXTENSION vector;` | RDS PG16 原生支持 |
| **Tair (Redis 兼容)** | `tair.scm.standard.4g.2db`(4G) | 高可用 1 主 1 从 |
| Tair 用途 | JWT 黑名单 / Arq broker / SMS 限频 / 配额预占 | 不存业务数据 |
| **OSS Bucket** `yaoqi-prod` | **private**,标准存储,与 ECS 同区域 | ACL 红线见 Checklist RL-03 |
| OSS 跨区复制 | 杭州 → 北京 备灾 | 生产开,staging 可不开 |
| OSS 生命周期 | `/exports/*` 7 天清,`/system-temp/*` 7 天清,归档案例 6 月转冷 | |
| OSS 服务端加密 | SSE-KMS | Checklist C-11 |

### 2.4 平台服务

| 资源 | 用途 | 备注 |
|---|---|---|
| **KMS** | 存放 secret(JWT_SECRET / DB 密码 / Azure key / OSS AK/SK) | Checklist F-04 / F-07 |
| **短信服务** | 验证码下发 | 模板审核 1-3 天;签名审核独立 |
| **OCR (RAM)** | 阿里云印刷文字识别 | 子账号开通 |
| **ACR(容器镜像服务)** | 私有镜像仓库 | 与 ECS 同区域免出口费 |
| **SLS(日志服务,P1)** | 应用日志聚合 | M4 先本地 + logrotate,P1 再上 SLS |
| **CMS(云监控)** | ECS / RDS / Tair 基础指标 + 告警 | 免费基础版够用 |
| **ICP 备案 + 域名** | 备案号挂域名 | 受理 7-20 天,**必须提前** |

### 2.5 RAM 子账号(工程师 / CI)

| 子账号 | 权限范围 |
|---|---|
| `yq-engineer-<name>` | ECS 只读 + ACR push/pull + RDS DML(staging) |
| `yq-ci` | ACR push + 部署脚本调用(无生产 DDL) |
| `yq-deploy` | ACR pull + ECS docker 操作 + KMS 读 |
| `yq-dba` | RDS DDL + 备份恢复(只主账号 + 1 名 DBA) |

**离职流程**:子账号 24h 内禁用 + 关联 STS 撤销 + 共享 secret 轮换。

---

## 3. Azure 资源准备

| 资源 | 配置 |
|---|---|
| **Azure Subscription** | 独立订阅,与公司其它项目分账(便于成本核算) |
| **Resource Group** | `yaoqi-prod-hk` / `yaoqi-staging-hk` |
| **Region** | **East Asia (Hong Kong)** — 合规通路 + 距离阿里云杭州 / 张北延迟可接受(< 60ms) |
| **Azure OpenAI Service** | Cognitive Service:`yaoqi-aoai-hk` |
| **Deployment 列表(staging + prod 各一套)** | `aoai-private-report` / `aoai-deployment-ocr-correct` / `aoai-deployment-image-summary` / `aoai-text-embedding-3-small` |
| **API Key** | 主 key + 备 key(轮换用) |
| **Networking** | 公网开,M4 不引入 Private Endpoint(成本与跨云 VPN 高);WAF 与限频在 Azure 侧默认 |
| **Quota** | 申请到位:Report deployment ≥ 30k TPM;Embedding ≥ 100k TPM |

> **私调 deployment**:微调模型由项目方在 Azure OpenAI Studio 训练 + 发布;发布后只把 deployment 名通过 KMS 注入 `Settings.aoai_deployment_report`,**不**改后端代码(见 [ai-integration-engineer.md §私调 deployment](../skills/ai-integration-engineer.md))。

---

## 4. 物料 / 账号 / 备案清单(对齐 tracker §2.4)

> 部署**前**必须收集齐;不全则该子项目无法开工。

| # | 物料 | 责任方 | 期望提供时间 | 状态 |
|---|---|---|---|---|
| 1 | 阿里云主账号 access 给 tech lead | 业务方 | 部署前 7 天 | ⚪ |
| 2 | 工程师子账号 + RAM 策略(见 §2.5) | 业务方 / DevOps | 部署前 3 天 | ⚪ |
| 3 | Azure 订阅 + OpenAI 资源 ownership 转交 | 业务方 | 部署前 7 天 | ⚪ |
| 4 | **域名所有权 + ICP 备案号** | 业务方 | **部署前 30 天**(备案 7-20 天) | ⚪ |
| 5 | 阿里云短信签名审核(品牌方 + 用途说明) | 业务方 | 部署前 7 天(审核 1-3 天) | ⚪ |
| 6 | 短信模板审核(登录验证码 / 通知 2 套) | 业务方 | 部署前 7 天 | ⚪ |
| 7 | OSS Bucket 名 + 区域(`yaoqi-prod` / 杭州) | 业务方 | 部署前 3 天 | ⚪ |
| 8 | 私调 Azure deployment 名(若已发布) | AI 工程方 | 上线前(没发布前用 `gpt-4o-mini` 顶) | ⚪ |
| 9 | KMS 加密所用主密钥 CMK ID | 业务方 / DevOps | 部署前 3 天 | ⚪ |
| 10 | 真实玉石 / 珠宝样本(图片 + 证书) | 业务方 | 上线前(用于 staging 真实 smoke) | ⚪ |
| 11 | 监控告警通道(企业微信 / 飞书 / 邮件 webhook) | 业务方 | 部署前 3 天 | ⚪ |
| 12 | 工程师跳板机 SSH 公钥白名单 | 全员 | 部署前 1 天 | ⚪ |

---

## 5. Secret 管理与 KMS 注入

> 红线见 [Security-Checklist §3.F](./Backend-Security-Checklist_v0.1.md):**任何 secret 禁入 git / 镜像 / `.env` 提交**。

### 5.1 Secret 清单

| Secret | 来源 | 轮换周期 |
|---|---|---|
| `DATABASE_URL`(含 DB 密码) | RDS 控制台生成 + KMS 加密 | 季度 |
| `REDIS_URL`(含 Tair 密码) | Tair 控制台 | 季度 |
| `JWT_SECRET` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` | 季度;轮换会让所有 session 失效 |
| `ALIYUN_OSS_ACCESS_KEY_ID` / `_SECRET` | RAM `yq-app-oss` 子账号 | 季度 |
| `ALIYUN_OCR_ACCESS_KEY_ID` / `_SECRET` | RAM `yq-app-ocr` 子账号 | 季度 |
| `ALIYUN_SMS_ACCESS_KEY_ID` / `_SECRET` | RAM `yq-app-sms` 子账号 | 季度 |
| `AOAI_API_KEY` | Azure 主 key,备 key 备用 | **月度**(跨云风险) |
| `AOAI_ENDPOINT` | `https://yaoqi-aoai-hk.openai.azure.com/` | 不变除非搬区 |
| `AOAI_DEPLOYMENT_REPORT` / `_OCR` / `_IMAGE_SUMMARY` / `_EMBEDDING` | Azure Studio 创建后填 | 微调升版才换 |

### 5.2 KMS 注入流程

```bash
# 1) 部署机(ECS-API)启动时,entrypoint 拉 secret
aliyun kms get-secret-value --secret-name yaoqi/prod/api > /tmp/.env.kms

# 2) entrypoint.sh 转环境变量后启动
set -a; source /tmp/.env.kms; set +a
rm /tmp/.env.kms                      # 用完即焚
exec gunicorn app.main:app ...
```

**禁止**:
- 把 `/tmp/.env.kms` 写到镜像
- `printenv` 进日志(过滤敏感 key)
- `docker inspect` 暴露 env(用 `--env-file` 不用 `-e`,且 file 在容器外)

### 5.3 `.env.example` 模板(随代码提交)

```env
# === 必填 ===
APP_ENV=production
APP_URL=https://api.yaoqi.<host>
DATABASE_URL=postgresql+asyncpg://yq_app:<password>@<rds-internal>:5432/yaoqi?sslmode=require
REDIS_URL=redis://:<password>@<tair-internal>:6379/0
JWT_SECRET=                              # secrets.token_urlsafe(32)

ALIYUN_OSS_REGION=oss-cn-hangzhou
ALIYUN_OSS_BUCKET=yaoqi-prod
ALIYUN_OSS_ACCESS_KEY_ID=
ALIYUN_OSS_ACCESS_KEY_SECRET=

ALIYUN_OCR_ACCESS_KEY_ID=
ALIYUN_OCR_ACCESS_KEY_SECRET=

ALIYUN_SMS_REGION=cn-hangzhou
ALIYUN_SMS_SIGN_NAME=曜齐
ALIYUN_SMS_TEMPLATE_LOGIN=SMS_xxxxxxxx
ALIYUN_SMS_ACCESS_KEY_ID=
ALIYUN_SMS_ACCESS_KEY_SECRET=

# === Azure OpenAI(跨云)===
AOAI_ENDPOINT=https://yaoqi-aoai-hk.openai.azure.com/
AOAI_API_KEY=
AOAI_API_VERSION=2024-10-21
AOAI_DEPLOYMENT_REPORT=aoai-private-report
AOAI_DEPLOYMENT_OCR=aoai-deployment-ocr-correct
AOAI_DEPLOYMENT_IMAGE_SUMMARY=aoai-deployment-image-summary
AOAI_DEPLOYMENT_EMBEDDING=aoai-text-embedding-3-small

# === Mock 开关(production 全 false)===
MOCK_AUTH=false
MOCK_OSS=false
MOCK_OCR=false
MOCK_AI=false
SEED_MOCK_DATA=false

# === RAG(M4 默认关)===
RAG_RECALL_ENABLED=false
```

---

## 6. 镜像构建与 ACR 流程

### 6.1 Dockerfile(权威版本)

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim-bookworm@sha256:<digest> AS base
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# 装系统依赖(libpq for asyncpg, build for some wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
      libpq5 ca-certificates curl tini \
    && rm -rf /var/lib/apt/lists/*

# 装 uv
RUN pip install --no-cache-dir uv==0.4.30

# 非 root 用户(Security-Checklist I-10)
RUN useradd -m -u 1000 appuser
WORKDIR /app

# 依赖层(改代码不重装依赖)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

# 代码层
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && chown -R appuser:appuser /app

USER appuser
ENTRYPOINT ["tini", "--", "/usr/local/bin/entrypoint.sh"]
CMD ["api"]                              # api | worker | migrate
```

`entrypoint.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
case "${1:-api}" in
  api)
    exec gunicorn app.main:app --workers 4 \
      --worker-class uvicorn.workers.UvicornWorker \
      --bind 0.0.0.0:8000 --timeout 60 --access-logfile -
    ;;
  worker)
    exec arq app.workers.arq_worker.WorkerSettings
    ;;
  migrate)
    exec alembic upgrade head
    ;;
  *)
    exec "$@"
    ;;
esac
```

### 6.2 镜像 tag 规则

- `registry.cn-hangzhou.aliyuncs.com/yaoqi/backend:<git-sha>`(每次 commit 推一个)
- `:staging`(staging 当前)
- `:prod`(prod 当前)
- `:<git-sha>` 永久保留;`:staging` / `:prod` 是 alias

**禁止**:`:latest`(Security-Checklist H-03)。

### 6.3 build & push(CI)

```bash
docker build \
  --build-arg APP_ENV=production \
  --tag registry.cn-hangzhou.aliyuncs.com/yaoqi/backend:${GIT_SHA} \
  -f backend/Dockerfile backend/

docker push registry.cn-hangzhou.aliyuncs.com/yaoqi/backend:${GIT_SHA}

# 漏洞扫描(Trivy)
trivy image --severity HIGH,CRITICAL --exit-code 1 \
  registry.cn-hangzhou.aliyuncs.com/yaoqi/backend:${GIT_SHA}
```

---

## 7. 数据库初始化与 Alembic 部署

### 7.1 首次初始化(每环境只跑一次)

```bash
# 1) RDS 控制台:创建 database `yaoqi`,owner `yq_migrate`
# 2) 装扩展(用 DDL 账号)
psql "$DATABASE_URL_DDL" <<SQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;
SQL

# 3) 跑 Alembic 到 head
docker run --rm \
  --env-file /etc/yaoqi/.env.runtime \
  registry.cn-hangzhou.aliyuncs.com/yaoqi/backend:${GIT_SHA} \
  migrate

# 4) 注入 super_admin(密码走 prompt,不留 history)
docker run --rm -it \
  --env-file /etc/yaoqi/.env.runtime \
  registry.cn-hangzhou.aliyuncs.com/yaoqi/backend:${GIT_SHA} \
  python -m app.scripts.bootstrap_admin --phone +86xxxxxxxxxxx
```

### 7.2 每次发版的 Alembic 流程

```bash
# 1) DBA review(若有 schema 变更)
docker run --rm --env-file ... yaoqi/backend:${NEW_SHA} \
  alembic upgrade head --sql > /tmp/pending.sql
# 把 pending.sql 发 DBA review;通过后:

# 2) 上线前 backup
pgbackrest --stanza=yaoqi backup --type=incr

# 3) 跑 migration(单点跑,不要在多台并发)
docker run --rm --env-file ... yaoqi/backend:${NEW_SHA} migrate

# 4) 失败回滚
docker run --rm --env-file ... yaoqi/backend:${OLD_SHA} \
  alembic downgrade -1
```

**红线**(对应 [Database-Schema §7.2](./Backend-Database-Schema_v0.1.md)):
- 破坏性变更分两步(加列双写 → 数据回填 → 删旧列)
- `alembic stamp head` **禁止**用于跳过 migration
- 生产手工 `ALTER TABLE` **禁止**,任何改动都必须走 revision

---

## 8. 应用部署(滚动更新)

### 8.1 单台 ECS 的 docker compose(`/etc/yaoqi/compose.yml`)

```yaml
services:
  api:
    image: registry.cn-hangzhou.aliyuncs.com/yaoqi/backend:${TAG}
    command: api
    env_file: /etc/yaoqi/.env.runtime
    ports: ["8000:8000"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8000/health"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 30s

  worker:
    image: registry.cn-hangzhou.aliyuncs.com/yaoqi/backend:${TAG}
    command: worker
    env_file: /etc/yaoqi/.env.runtime
    restart: unless-stopped
```

> Worker 只在 ECS-Worker 上跑,API 容器只在 ECS-API 上跑。

### 8.2 滚动更新流程(生产 2 台 API)

```bash
# === 在 ECS-API-1 ===
# 1) 拉新镜像
docker compose -f /etc/yaoqi/compose.yml pull api

# 2) SLB 摘流(健康检查超时 30s,提前 30s 标 down)
aliyun slb set-backend-server --server-id <ecs-api-1> --weight 0

# 3) 滚动 api
TAG=${NEW_SHA} docker compose up -d api

# 4) 等 /health 通,自检 1 分钟
sleep 60 && curl -fsS http://localhost:8000/health

# 5) SLB 加回
aliyun slb set-backend-server --server-id <ecs-api-1> --weight 100

# === 在 ECS-API-2 重复 1-5 ===

# === ECS-Worker ===
TAG=${NEW_SHA} docker compose up -d worker
# Worker 重启时,在跑的 job 会被 arq 优雅重试(`max_tries`);
# 若有长任务,先 SIGTERM + 等 grace period 60s
```

### 8.3 应急回滚

```bash
# 镜像回滚(secret 不变)
TAG=${OLD_SHA} docker compose up -d api worker

# DB 回滚(仅在 schema 变更失败时)
docker run --rm --env-file ... yaoqi/backend:${OLD_SHA} \
  alembic downgrade -1
```

**回滚 SLA**:发现问题 → 5 分钟内开始回滚 → 10 分钟内恢复。

---

## 9. 网络配置(SLB / HTTPS / WAF)

### 9.1 SSL 证书

- 从阿里云**SSL 证书服务**申请(免费 DV 证书 12 个月,或买 OV / EV)
- 挂在 SLB 上(SSL 卸载在 SLB,后端 ECS 收 HTTP 即可,内网安全)
- TLS ≥ 1.2,禁用弱套件(Security-Checklist I-02)

### 9.2 SLB 监听规则

| 监听端口 | 后端协议 | 后端端口 | 转发规则 |
|---|---|---|---|
| 443 (HTTPS) | HTTP | 8000 | 默认转 ECS-API * 2 |
| 80 (HTTP) | — | — | 301 重定向 → `https://$host$request_uri` |

### 9.3 必加响应头(Nginx 边车 或 FastAPI middleware)

```python
# app/middleware/security_headers.py
@app.middleware("http")
async def security_headers(request, call_next):
    resp = await call_next(request)
    resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' https://*.aliyuncs.com data:; "
        "script-src 'self'; style-src 'self' 'unsafe-inline'"
    )
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return resp
```

### 9.4 WAF 规则

阿里云 WAF 开启:
- OWASP Top 10 默认规则集
- CC 防护(同 IP 60s ≥ 200 请求拦截)
- SQL 注入 / XSS 内置规则
- 短信接口路径 `/api/auth/sms` 单独限频规则(60s ≤ 5 / IP)

---

## 10. 跨云出口配置

### 10.1 安全组放行

```bash
# sg-api / sg-worker 出方向追加
# 协议: TCP / 端口: 443 / 目标: 0.0.0.0/0(简单做法)
# 严格做法(推荐): 仅放 Azure HongKong IP 段
```

Azure 公网 IP 段:`https://www.microsoft.com/en-us/download/details.aspx?id=56519`(`AzureCloud.eastasia` JSON)— 季度刷新一次。

### 10.2 跨云调用规范(代码层)

| 项 | 设置 |
|---|---|
| `httpx.AsyncClient(timeout=60.0)` | API 端到端 60s 上限 |
| `tenacity.retry(stop_after_attempt(3), wait_exponential(min=1, max=8))` | 跨云抖动重试 |
| `ai_call_logs.latency_ms` | 必填,事后归因 |
| **不**引入 API Gateway / VPN 专线 | M4 拍板;若 P95 > 30s 持续 1 天再加 |

### 10.3 跨云延迟基线(测一次记下来)

```bash
# 在 ECS-API 上
curl -w "@curl-format.txt" -o /dev/null -s \
  https://yaoqi-aoai-hk.openai.azure.com/openai/deployments/?api-version=2024-10-21
```

期望:DNS < 50ms / connect < 100ms / TLS < 200ms / total < 500ms(无业务负载时)。

---

## 11. 监控告警

### 11.1 健康检查 `/health`

```python
# app/api/health.py
@router.get("/health")
async def health(db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)):
    return {
        "ok": True,
        "checks": {
            "db": await _check_db(db),
            "redis": await _check_redis(redis),
            "oss": await _check_oss(),
            "azure_openai": await _check_azure(),
        },
    }
```

SLB 健康检查走 `/health`(返 200 才算健康)。

### 11.2 阿里云 CMS(必接)

| 指标 | 阈值 | 通道 |
|---|---|---|
| ECS CPU > 80% 持续 5min | 告警 | 企业微信 + 邮件 |
| ECS 磁盘 > 80% | 告警 | 同上 |
| RDS 连接数 > 80%(`max_connections`) | 告警 | 同上 + 短信 |
| RDS 慢查询 > 10 / min | 告警 | 邮件 |
| Tair 命中率 < 90% | 提示 | 邮件 |
| SLB 4xx 率 > 5% 持续 5min | 告警 | 同上 |
| SLB 5xx 率 > 1% 持续 1min | **紧急** | 同上 + 短信 + 电话 |

### 11.3 应用层指标(P1,Prometheus)

```python
# 关键指标(由 prometheus_fastapi_instrumentator 暴露)
http_request_duration_seconds_p95     # < 1s
ai_call_total{status="failed"} rate   # < 10% / 5min
arq_jobs_queued                       # < 1000 持续 10min 告警
ai_monthly_cost_cents                 # 月预算 80% 告警
```

详见 [Security-Checklist §3.G](./Backend-Security-Checklist_v0.1.md) G-08 / G-09 / G-10。

### 11.4 日志聚合(M4 本地,P1 SLS)

- M4:每台 ECS 本地 `/var/log/yaoqi/*.log` + `logrotate`(7 天)
- P1:接 SLS,关键字告警(`request_id` 全链路追踪)

---

## 12. 备份与恢复

### 12.1 RDS 自动备份

- 阿里云 RDS 控制台:**每日全量** + **保留 14 天** + **跨区域备份**
- 自定义备份(P0 上线前):`pgbackrest` 在 ECS-Jump 上跑,推 OSS 冷归档

### 12.2 OSS 备份

- 跨区域复制:杭州 → 北京
- 删除策略:**禁用** OSS 默认删除;走应用层标 `deleted_at`(对应 schema §9.4)

### 12.3 恢复演练(**季度一次,必须做**)

```bash
# 1) 在 staging 环境
# 2) 从前一天备份恢复一个新 RDS 实例
aliyun rds create-from-backup --backup-id <id> --new-instance yaoqi-restore-test

# 3) 跑 smoke test
docker run --rm --env DATABASE_URL=<restore-url> ... yaoqi/backend:prod \
  pytest tests/smoke/

# 4) 计时:RTO 目标 < 1h,RPO 目标 < 6h
```

**没演练过的备份 = 没备份**。每次演练记到 `docs/audit/recovery-drill-YYYY-MM-DD.md`。

---

## 13. CI/CD Pipeline

### 13.1 CI 必跑(每 PR)

```yaml
# .github/workflows/ci.yml(示意)
jobs:
  backend:
    steps:
      - uses: actions/checkout@v4
      - run: uv sync --dev
      - run: uv run ruff check .
      - run: uv run mypy app/
      - run: uv run pytest --cov=app --cov-fail-under=70
      - run: uv run alembic check          # 阻止 pending 漂移
      - run: gitleaks detect --source .
      - run: pip-audit
      - run: docker build -t test backend/
      - run: trivy image --severity HIGH,CRITICAL --exit-code 1 test
```

### 13.2 CD(merge to main → staging,手动 promote → prod)

```yaml
# .github/workflows/deploy.yml(示意)
jobs:
  build-and-push:
    if: github.ref == 'refs/heads/main'
    steps:
      - run: docker build -t registry.cn-hangzhou.aliyuncs.com/yaoqi/backend:${{ github.sha }} backend/
      - run: docker push registry.cn-hangzhou.aliyuncs.com/yaoqi/backend:${{ github.sha }}

  deploy-staging:
    needs: build-and-push
    steps:
      - run: ssh ecs-staging "cd /etc/yaoqi && TAG=${{ github.sha }} docker compose up -d"

  deploy-prod:
    needs: deploy-staging
    environment: production              # GitHub environment 卡人工 approve
    steps:
      - run: ssh ecs-api-1 "..."
      - run: ssh ecs-api-2 "..."
```

### 13.3 上线频率与窗口

- **staging**:每次 merge 自动
- **production**:**工作日上午 10-11 点**(出问题人都在)
- **禁止**:周五下午 / 假期前 / 凌晨上线(除非紧急修复)

---

## 14. 应急剧本(摘要,详 [Security-Checklist §6](./Backend-Security-Checklist_v0.1.md))

| 场景 | 第一步 | 补救 |
|---|---|---|
| Secret 泄露 | revoke 全部 secret + 换 JWT_SECRET(让所有 session 失效) | 查 audit log + 通知 |
| SQL 注入告警 | WAF 拉黑 IP + 下线问题接口 | 修代码 + sqlmap 复测 |
| OSS ACL 被改公开 | **立即**改回 private | 查 24h 内访问 + 通知用户 |
| AI 调用激增烧钱 | 临时调低 `quota_service` 全局上限 | 锁定来源用户 + 封号 |
| 主 ECS 宕 | SLB 自动摘流;手动起备机 | 复盘根因 |
| RDS 主库宕 | 阿里云自动主从切换(30s 内) | 验证 + 通知 |
| 跨云 Azure 不通 | `tenacity` 自动重试 3 次 → 失败返 `ai.upstream_unavailable` | 监控 latency 看是否恢复 |

回滚 SLA(§8.3 重申):**5 min 内开始 + 10 min 内恢复**。

---

## 15. 上线 Checklist(production 第一次发版必走)

### 15.1 上线前(T-7 天 ~ T-1 天)

- [ ] §4 物料清单全部 ✅(尤其 ICP 备案)
- [ ] §2 阿里云资源开齐 + 安全组配好
- [ ] §3 Azure 资源开齐 + quota 申请到
- [ ] §5 secret 全部入 KMS,`.env.example` 与 `Settings` 对齐(F-08)
- [ ] [Security-Checklist §1 红线](./Backend-Security-Checklist_v0.1.md) 8 条 100%
- [ ] [Security-Checklist §3 P0 项](./Backend-Security-Checklist_v0.1.md) 100% 通过
- [ ] 备份恢复演练做过一次(§12.3)
- [ ] 应急通道(企微 / 飞书 / 电话)测过
- [ ] `tests/test_rbac_redlines.py` 100% 行覆盖

### 15.2 上线当天(T-Day)

- [ ] 时间窗在工作日 10-11 点
- [ ] DBA on-call + DevOps on-call + 业务方知情
- [ ] 跑一次最新备份(`pgbackrest --type=incr backup`)
- [ ] 跑 Alembic dry-run(`--sql > pending.sql`)给 DBA 看
- [ ] 滚动部署(§8.2)
- [ ] 部署后:
  - [ ] `/health` 全绿
  - [ ] smoke test(登录 / 创建案例 / OCR / 报告 / customer-brief / admin 看原图留痕)
  - [ ] 监控面板:CPU / 内存 / DB 连接 / SLB 5xx 全正常
  - [ ] 跑一次跨云 Azure 调用,看 `ai_call_logs.latency_ms`

### 15.3 上线后(T+1 ~ T+7)

- [ ] 7×24 监控 1 周
- [ ] 每日看 `admin_operation_logs` / `ai_call_logs` 失败率
- [ ] T+7 复盘:成本 / 性能 / 用户反馈

---

## 16. 未决项(与 tracker §二 对齐)

详见 [docs/discussions/M4-backend-rollout-tracker.md §二](./discussions/M4-backend-rollout-tracker.md):

- [ ] §2.4 全部 12 项物料(本文 §4 表格全为 ⚪)— 业务方排期
- [ ] §2.5 AI 工程接手时机 — 影响 §3 Azure deployment 是否真名 vs `gpt-4o-mini` 顶
- [ ] §2.6 前端双写期灰度策略 — 影响 §8 滚动流程是否需要双跑 mock + 真后端
- [ ] WAF 是否上(§9.4)— 阿里云 WAF 实例费,业务方拍
- [ ] SLS 是否 M4 直接上(§11.4)— 还是 P1 再上

---

## 维护规则

1. **每次部署相关变更**(资源规格 / 镜像 tag 规则 / 滚动步骤 / KMS 名)— 本文优先更新
2. 物料 §4 状态在每次开协调会后刷新
3. 上线 checklist §15 每次发版**实际打勾**贴到 PR / Release notes
4. 应急剧本 §14 每出一次事件后**更新一次**(实战经验沉淀)
5. M4 实施开工后,本文随 IaC(Terraform / Pulumi)落地的部分迁到 `backend/infra/README.md`,本文保留**决策与流程**部分
