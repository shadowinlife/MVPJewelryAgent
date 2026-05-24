# 曜齐 YAOQI — Backend Security Checklist v0.1

> M4 安全验收清单。把 [Backend-Architecture §10.3 四条红线](./Backend-Architecture_v0.1.md) + [Product-Spec §14 OSS 安全](./Product-Spec_v0.4.md) + [§16 报告权限](./Product-Spec_v0.4.md) + [Technical-Spec §4.2 权限原则](./Technical-Spec_v0.1.md) **扩展为可逐项核对的渗透测试清单**。
>
> 父文档:[Backend-Architecture_v0.1.md](./Backend-Architecture_v0.1.md) / [Backend-Database-Schema_v0.1.md](./Backend-Database-Schema_v0.1.md)
> 兄弟:[skills/backend-engineer.md §禁止事项](../skills/backend-engineer.md) / [skills/ai-integration-engineer.md §禁止事项](../skills/ai-integration-engineer.md)
> 起始:2026-05-22

---

## 0. 文档定位

| 在哪 | 内容 |
|---|---|
| Backend-Architecture §10.3 | 4 条 RBAC 红线(裁剪 / 越权 / 客户简洁版 / admin 留痕)— 简要 |
| Product-Spec §14 / §16 | OSS 私有 + 报告分级裁剪 + 客户简洁版禁公开 URL — 业务侧表达 |
| Technical-Spec §4.2 | 权限七条 — 早期版本(以本文为准) |
| **本文档** | 渗透 / 自动化 / 应急响应**逐项可核对**;每条带 `ID / 描述 / 验证 / 严重度 / 状态` |

**仲裁顺序**:本文 ≻ Backend-Architecture §10.3 ≻ Product-Spec §14/§16 ≻ Technical-Spec §4.2。
**用法**:M4 阶段验收必须把本文每一行都核对一遍并贴在 PR description;M5 上线前再走一遍渗透红线(§5)。

---

## 1. 红线总览(违反 = 阻塞上线)

> 这 8 条是**全局阻塞红线**,任何一条 fail 都不允许上 production,且 staging 上发现 24h 内必须修。

| ID | 红线 | 出处 | 自动化测试 |
|---|---|---|---|
| RL-01 | 报告字段裁剪必须在后端,**禁止**前端隐藏 | [Backend-Architecture §10.3](./Backend-Architecture_v0.1.md) / [Product-Spec §16](./Product-Spec_v0.4.md) | `test_rbac_redlines.py::test_free_user_report_excludes_premium_fields` |
| RL-02 | 用户**不得**读他人 `cases / reports / files`(GET / PATCH / DELETE 全防) | [Backend-Architecture §10.3](./Backend-Architecture_v0.1.md) | `test_rbac_redlines.py::test_cross_user_case_access_returns_403` |
| RL-03 | OSS Bucket **私有**;**禁止** public-read / public-read-write;不返回原始永久 URL | [Product-Spec §14.1](./Product-Spec_v0.4.md) | `test_oss_security.py::test_bucket_acl_is_private` |
| RL-04 | 客户简洁版**不**生成对外 URL,**必须登录**才能查 | [Product-Spec §16.3](./Product-Spec_v0.4.md) | `test_rbac_redlines.py::test_customer_brief_requires_login` |
| RL-05 | 管理员看原图 / 导出 / 改会员等高敏操作**必须**写 `admin_operation_logs` | [Backend-Architecture §10.3](./Backend-Architecture_v0.1.md) | `test_rbac_redlines.py::test_admin_export_writes_audit_log` |
| RL-06 | 短信 / 验证码接口**强制限频**;同手机号 60s 内只能 1 次 | [skills/backend-engineer.md 红线6](../skills/backend-engineer.md) | `test_sms_rate_limit.py::test_60s_throttle` |
| RL-07 | 任何 secret(API Key / DB 密码 / JWT_SECRET / Azure key)**禁入代码 / 镜像 / git**;生产 env 走阿里云 KMS | [Technical-Spec §3.3](./Technical-Spec_v0.1.md) | CI `gitleaks` + `trufflehog`,失败阻塞 merge |
| RL-08 | 导出 / 列表接口默认 `WHERE is_mock=false`;`?include_mock=true` 需二次确认 | [skills/backend-engineer.md 红线7](../skills/backend-engineer.md) | `test_export_excludes_mock.py` |

---

## 2. 责任矩阵(RACI)

| 类别 | 红线条 ID | R (执行) | A (问责) | C (咨询) | I (告知) |
|---|---|---|---|---|---|
| RBAC / 裁剪 | RL-01 / RL-02 / RL-04 / RL-05 | backend-engineer | tech lead | ai-integration-engineer | 业务方 |
| OSS | RL-03 | backend-engineer | tech lead | DevOps | 业务方 |
| 短信限频 | RL-06 | backend-engineer | tech lead | — | — |
| Secret | RL-07 | DevOps + backend-engineer | tech lead | 业务方(KMS 授权) | 全员 |
| Mock 隔离 | RL-08 | backend-engineer | tech lead | QA | — |
| 渗透测试 | §5 全部 | 外部第三方 / 安全顾问 | tech lead | backend-engineer | 业务方 |
| 应急响应 | §6 | on-call backend | tech lead | DevOps | 业务方 + 全员 |

---

## 3. 检查清单(按类目)

> 每项格式:`[ID] 描述 / 验证方法 / 严重度 (P0/P1/P2) / 状态`
> 状态:⚪ 未实现 / 🟡 部分 / 🟢 已通过 / 🔴 失败

### 3.A 认证与会话

| ID | 项 | 验证 | 严重度 | 状态 |
|---|---|---|---|---|
| A-01 | 用户 session = `yq_session` cookie,`HttpOnly + Secure + SameSite=Lax` | 浏览器 devtools 查 cookie 属性;`Set-Cookie` 响应头含三标志 | P0 | ⚪ |
| A-02 | 管理员 session = `yq_admin` cookie,过期 12h,用户 7d | JWT decode 看 `exp`;过期后请求返 401 | P0 | ⚪ |
| A-03 | JWT 签名算法固定 `HS256`,**禁止** `none` / `alg=` 注入 | 改 `alg: none` 的伪造 token → 401 | P0 | ⚪ |
| A-04 | Logout 后 `jti` 入 Redis 黑名单,TTL = 原 token 剩余 | logout 后用旧 cookie 请求 → 401 | P0 | ⚪ |
| A-05 | 管理员密码 `passlib[bcrypt] rounds=12` | 数据库 `users.password_hash` 形如 `$2b$12$...` | P0 | ⚪ |
| A-06 | 短信验证码:6 位、5 min 有效、明文不落库(只存 hash) | `sms_codes.code_hash` 非明文;过期后无法使用 | P0 | ⚪ |
| A-07 | 同手机号 60s 内只能发 1 次(RL-06) | 连发两次 → 第二次 429 | P0 | ⚪ |
| A-08 | 错误验证码连续 5 次锁号 30 分钟 | `sms_codes.attempts >= 5` 后查码必失败 | P1 | ⚪ |
| A-09 | 登录失败提示**不区分**"用户不存在 / 密码错"(防枚举) | 错误手机 / 错验证码,响应文案一致 | P1 | ⚪ |
| A-10 | 用户密码字段(未来加)永远不在任何 response_model 出现 | grep schema 文件无 `password` 字段 | P0 | ⚪ |

### 3.B 鉴权与 RBAC

| ID | 项 | 验证 | 严重度 | 状态 |
|---|---|---|---|---|
| B-01 | 路由层走 `Depends(require_user)` / `require_admin` / `require_tier`;**禁止**手写 if-else | grep `if user.role` 在 api/ 下应为 0 | P0 | ⚪ |
| B-02 | `cropper_for_user(report, tier)` 是唯一裁剪入口(RL-01) | grep 前端 `if (membership === ...)` 隐藏字段应为 0 | P0 | ⚪ |
| B-03 | `ReportFree/Basic/Pro/Business/BusinessPro/Admin/CustomerBrief` 7 个 Pydantic 类**物理排除**未声明字段 | 单测:free_user 拉报告,`'priceRange' not in response.json()` | P0 | ⚪ |
| B-04 | GET `/api/cases/:case_no` 校验 `case.user_id == current_user.id` or admin(RL-02) | 跨用户访问 → 403 | P0 | ⚪ |
| B-05 | PATCH / DELETE 同 B-04 | 同上 | P0 | ⚪ |
| B-06 | `/api/customer-brief/:id` 强制 `require_user`(RL-04) | 无 session 访问 → 401 | P0 | ⚪ |
| B-07 | 客户简洁版接口**禁止**生成永久 URL / public link | 响应不含 `share_url` / `public_link` 字段 | P0 | ⚪ |
| B-08 | `/admin/**` 走 `require_admin`;super_admin 专属路径走 `require_super_admin` | 普通 admin 访问 super 路径 → 403 | P0 | ⚪ |
| B-09 | RBAC 矩阵的 4 条红线自动化覆盖(对应 Backend-Architecture §10.3) | `tests/test_rbac_redlines.py` 覆盖 ≥ 4 case | P0 | ⚪ |
| B-10 | 新增 RBAC 规则**必须**同步加 test_rbac_redlines.py 用例 | PR review checklist | P1 | ⚪ |

### 3.C OSS 与文件

| ID | 项 | 验证 | 严重度 | 状态 |
|---|---|---|---|---|
| C-01 | Bucket ACL = `private`,**禁止** public-read / public-read-write(RL-03) | `aliyun oss bucket-info <bucket>` 输出 `ACL: private` | P0 | ⚪ |
| C-02 | 不返回 `oss_key_original` 字段给前端任何 user 端接口 | grep `response_model` 与 `oss_key_original` 共现应仅在 admin/ 下 | P0 | ⚪ |
| C-03 | 普通用户拿到的图片 URL 5 min 内过期 | 生成 URL → wait 6 min → 403 | P0 | ⚪ |
| C-04 | 管理员看原图走 `/admin/cases/:id/original-image`,**强制**写 `admin_operation_logs`(RL-05) | 调用后查表有新行 `action='view_original_image'` | P0 | ⚪ |
| C-05 | STS Token 签发 policy 硬编码 `key_prefix = user-upload-*/{me.user_id}/` | 前端伪造他人 user_id → 上传 403 | P0 | ⚪ |
| C-06 | STS Token 限制 `max-size`(图片 ≤ 20 MB / pdf ≤ 50 MB) | 超大文件上传 → 阿里云拒绝 | P0 | ⚪ |
| C-07 | STS Token TTL ≤ 5 min | policy expire 字段 ≤ 300s | P0 | ⚪ |
| C-08 | OSS 回调端点验签(`x-oss-callback-signature`) | 伪造 callback → 403 | P0 | ⚪ |
| C-09 | 用户预览默认拿 `oss_key_watermarked`;水印含案例号 + 用户尾号(Product-Spec §14.3) | 视觉抽检 + 单测拼接水印参数 | P1 | ⚪ |
| C-10 | OSS Bucket 与 ECS 同区域,避免出口费 | `aliyun oss bucket-info` region 与 ECS region 一致 | P2 | ⚪ |
| C-11 | OSS 服务端加密(SSE-KMS)开启 | `aliyun oss get-bucket-encryption` 输出 KMS 模式 | P1 | ⚪ |
| C-12 | OSS 生命周期:`/exports/*` 7 天清,`/system-temp/*` 7 天清 | `aliyun oss get-bucket-lifecycle` 看规则 | P1 | ⚪ |

### 3.D 数据库与注入

| ID | 项 | 验证 | 严重度 | 状态 |
|---|---|---|---|---|
| D-01 | 全 SQL 走 SQLAlchemy 2.0 `select() / params={}`,**禁止**字符串拼 SQL | grep `f"SELECT ... {var}"` / `+ ` 拼 SQL 应为 0 | P0 | ⚪ |
| D-02 | `text("...")` 必须带 `:bindparam`,**禁止**字符串插值 | grep `text(f"..."` 应为 0 | P0 | ⚪ |
| D-03 | Alembic raw SQL 也走 `op.execute(text("..."), {...})` | grep migrations 同 D-02 | P0 | ⚪ |
| D-04 | 全文搜索走 `to_tsvector('simple', ...)`,**禁止**前端字符串直拼 ts_query | service 层手动转义 `&` `|` `!` | P1 | ⚪ |
| D-05 | DB 账号最小权限:应用账号只有 CRUD,无 DDL(DDL 走 migration 专用账号) | RDS 控制台查 grants | P0 | ⚪ |
| D-06 | 应用账号**不持**生产备份导出权限 | 同上 | P0 | ⚪ |
| D-07 | DB 连接强制 SSL(`sslmode=require`) | `database_url` 含 `?sslmode=require` | P0 | ⚪ |
| D-08 | 事务隔离级别 = `READ COMMITTED`(默认,业务无需 SERIALIZABLE) | `SHOW transaction_isolation` | P2 | ⚪ |
| D-09 | 长事务监控(> 30s 告警) | Prometheus rule | P1 | ⚪ |
| D-10 | RDS 慢查询日志开启,> 500ms 报警 | RDS 控制台 + 报警 | P1 | ⚪ |

### 3.E 限频与防滥用

| ID | 项 | 验证 | 严重度 | 状态 |
|---|---|---|---|---|
| E-01 | 短信验证码 60s 限频(RL-06) | A-07 重复 | P0 | ⚪ |
| E-02 | 登录接口 IP 限频(60s 内同 IP ≤ 10) | Redis `login:ip:{ip}` 计数 | P1 | ⚪ |
| E-03 | AI 报告生成接口配额硬上限(对应 `token_quotas`) | 超配 → 403 `quota_exceeded` | P0 | ⚪ |
| E-04 | OSS STS 接口同 user 5s 限频(防大批量伪造 case_id 探测) | 单测 | P1 | ⚪ |
| E-05 | OCR 触发接口配额(同 case_id 1h 内 ≤ 5 次) | 防重复跑 OCR 烧钱 | P1 | ⚪ |
| E-06 | 全接口默认 Uvicorn 并发限流(`--limit-concurrency 100`) | Gunicorn config | P2 | ⚪ |
| E-07 | `429` 返回信封带 `Retry-After` header | `httpx.AsyncClient` 测试 | P1 | ⚪ |
| E-08 | 验证码错误 5 次锁定(A-08) | A-08 重复 | P1 | ⚪ |

### 3.F 密钥与配置

| ID | 项 | 验证 | 严重度 | 状态 |
|---|---|---|---|---|
| F-01 | git 历史无任何 `.env` 真实值(RL-07) | `gitleaks detect --source .` 退出码 = 0 | P0 | ⚪ |
| F-02 | 镜像内无任何 secret(`docker history` 检查) | CI 步骤 | P0 | ⚪ |
| F-03 | `Settings` 全部走 `pydantic-settings` 读 env,grep 不应见 `os.environ.get` 散落 | grep `os.environ` 在 app/ 下 ≤ 1(只在 `core/config.py`) | P0 | ⚪ |
| F-04 | 生产 env 从阿里云 KMS 注入(不走 `.env` 文件) | 部署脚本走 `aliyun kms get-secret-value` | P0 | ⚪ |
| F-05 | KMS 凭据轮换季度一次 | 运维 checklist + 改 env + 滚动重启 | P1 | ⚪ |
| F-06 | `JWT_SECRET` 至少 32 字节随机(`secrets.token_urlsafe(32)`) | 生成命令归档 | P0 | ⚪ |
| F-07 | Azure OpenAI Key 单独 KMS key 加密,与 OSS / DB key 不共用 | KMS 控制台 | P0 | ⚪ |
| F-08 | `.env.example` 与 `Settings` 字段同步;新增字段必须同时改两处 | PR review 卡 | P1 | ⚪ |
| F-09 | 子账号不持有 OSS / RDS / OCR / SMS 完整权限,只发短期 STS | RAM 控制台 | P0 | ⚪ |
| F-10 | 工程师离职 → 子账号 24h 内禁用 + 关联 STS 撤销 | 离职 checklist | P0 | ⚪ |

### 3.G 审计与可观测

| ID | 项 | 验证 | 严重度 | 状态 |
|---|---|---|---|---|
| G-01 | `admin_operation_logs` **永久禁删**;DB user 无 `DELETE` 权 | DB grant 检查 | P0 | ⚪ |
| G-02 | 中间件 `AuditMiddleware` 挂在 `/admin/**`,自动写日志 | 抓 trace 看每次 admin 请求都有新行 | P0 | ⚪ |
| G-03 | 高敏 action 枚举固定(见 schema §5.4 CHECK 约束) | DB CHECK 拒绝未知 action | P1 | ⚪ |
| G-04 | `request_id` 中间件:每个请求生成 UUID,日志全链路带 | grep 日志含 `request_id=` | P1 | ⚪ |
| G-05 | `ai_call_logs` 写入所有 AI 调用(含失败),`latency_ms` 必填 | 跨云慢查询溯源依赖此 | P0 | ⚪ |
| G-06 | 错误日志不含 PII(手机号 / 密码 / Azure key) | 抽样 + Filebeat filter | P0 | ⚪ |
| G-07 | `/health` 暴露 DB / Redis / OSS / Azure OpenAI 连通性 | `curl /health` 返各项 status | P1 | ⚪ |
| G-08 | Prometheus 指标:P95 latency / AI 成功率 / 队列堆积 | Grafana board | P1 | ⚪ |
| G-09 | AI 调用失败率 > 10% 持续 5min → 报警 | AlertManager rule | P1 | ⚪ |
| G-10 | 月度成本超预算 80% → 报警(`ai_call_logs` 聚合 cron) | cron + 告警通道 | P1 | ⚪ |

### 3.H 依赖与供应链

| ID | 项 | 验证 | 严重度 | 状态 |
|---|---|---|---|---|
| H-01 | `uv.lock` 提交 git,版本固定 | git 含 `uv.lock` | P0 | ⚪ |
| H-02 | CI 跑 `pip-audit` / `safety check`,高危漏洞阻塞 merge | CI step | P0 | ⚪ |
| H-03 | 镜像基座固定版本(`python:3.12-slim-bookworm@sha256:...`),**禁止** `:latest` | Dockerfile grep `:latest` 为 0 | P0 | ⚪ |
| H-04 | Dependabot / Renovate 周报评估 | GitHub setting | P1 | ⚪ |
| H-05 | 第三方包来源仅 PyPI 官方,**禁止** git+url 装(供应链风险) | grep `pyproject.toml` 无 `git+` | P1 | ⚪ |
| H-06 | 镜像漏洞扫描(Trivy / Snyk),严重漏洞阻塞发布 | CI step | P0 | ⚪ |

### 3.I 传输与基础设施

| ID | 项 | 验证 | 严重度 | 状态 |
|---|---|---|---|---|
| I-01 | 全站强制 HTTPS;HTTP 301 重定向 | `curl -I http://...` 返 301 | P0 | ⚪ |
| I-02 | TLS ≥ 1.2,禁用 TLS 1.0/1.1 + 弱加密套件 | SSL Labs 评分 ≥ A | P0 | ⚪ |
| I-03 | HSTS 头 `max-age=31536000; includeSubDomains` | `curl -I` 看 header | P1 | ⚪ |
| I-04 | `X-Frame-Options: DENY` / `X-Content-Type-Options: nosniff` | 同上 | P1 | ⚪ |
| I-05 | CSP 头(`default-src 'self'; img-src ... oss.aliyuncs.com`) | 同上 | P1 | ⚪ |
| I-06 | SLB / WAF 开启 OWASP 规则集 | 阿里云 WAF 控制台 | P1 | ⚪ |
| I-07 | RDS / Redis / OSS 网络 ACL 只放 ECS 内网段 | VPC 安全组规则 | P0 | ⚪ |
| I-08 | RDS 不开公网,Tair 不开公网 | RDS / Tair 控制台 | P0 | ⚪ |
| I-09 | SSH 走跳板机 + 密钥;**禁止**密码登录 / 22 端口公网 | sshd_config 检查 | P0 | ⚪ |
| I-10 | 应用容器以非 root 运行(Dockerfile `USER appuser`) | `docker inspect` 看 User | P1 | ⚪ |

### 3.J 跨云出口与 AI

| ID | 项 | 验证 | 严重度 | 状态 |
|---|---|---|---|---|
| J-01 | 调 Azure 一律 `*.openai.azure.com`,**禁止** `api.openai.com` | grep 代码无 `api.openai.com` | P0 | ⚪ |
| J-02 | Azure 调用 `timeout=60s` + `tenacity` 指数退避(`max_attempts=3`) | 代码 review + `ai_call_logs.latency_ms` 抽样 | P0 | ⚪ |
| J-03 | Azure deployment 名**禁止**硬编码 | grep `aoai-private-report` / `gpt-4o` / `gpt-4o-mini` 在 app/ 下应仅在 `core/config.py` schema | P0 | ⚪ |
| J-04 | Prompt 模板**禁止**塞 PII(原始手机号 / 身份证) | `rendering.py` 输入清洗 + 单测 | P0 | ⚪ |
| J-05 | AI 调用走 `quota_service.reserve → call → settle/release` 三段式 | grep `llm.generate` 必前后有 reserve/settle | P0 | ⚪ |
| J-06 | `ai_call_logs` 每次写(含失败,`status='failed'` + `error_message`) | G-05 重复 | P0 | ⚪ |
| J-07 | Azure API Key 通过 `SecretStr` 包装,`__repr__` 不泄漏 | `repr(settings)` 输出 `aoai_api_key=SecretStr('**********')` | P1 | ⚪ |
| J-08 | RAG 召回开关默认 `Settings.rag_recall_enabled=False`(M4) | grep config 默认值 | P1 | ⚪ |
| J-09 | Azure region 锁 `HongKong`(合规通路) | Settings `aoai_endpoint` 含 `hongkong` 或对应域 | P0 | ⚪ |
| J-10 | Azure 失败不向用户回显原始错误(防泄漏 endpoint / deployment 名) | service 层翻译为 `ai.upstream_unavailable` | P1 | ⚪ |

---

## 4. 自动化测试映射

> 后端 CI 必跑;失败阻塞 merge。

| 测试文件 | 覆盖 ID |
|---|---|
| `tests/test_rbac_redlines.py` | RL-01, RL-02, RL-04, RL-05, B-01~B-09 |
| `tests/test_oss_security.py` | RL-03, C-01~C-08 |
| `tests/test_sms_rate_limit.py` | RL-06, A-07, A-08, E-01, E-08 |
| `tests/test_auth_session.py` | A-01~A-06, A-09, A-10 |
| `tests/test_export_excludes_mock.py` | RL-08 |
| `tests/test_quota_lifecycle.py` | E-03, J-05 |
| CI:`gitleaks` + `trufflehog` | RL-07, F-01 |
| CI:`pip-audit` + Trivy | H-02, H-06 |
| CI:`ruff` + `mypy --strict` | 代码质量基线 |

**Coverage gate**(M4 入闸):
- `tests/test_rbac_redlines.py` 行覆盖 100%,**任何 PR 不得降低**
- 整库覆盖 ≥ 70%(service 层 ≥ 85%)

---

## 5. 渗透测试清单(M5 上线前必跑一次)

> 由外部安全顾问 / 独立 QA 跑,**不**由开发者自测。

### 5.1 工具与方法

- **OWASP ZAP** 自动扫描(被动 + 主动)
- **Burp Suite** 手工拦截重放(重点 RBAC / OSS / 越权)
- **Nuclei** 漏洞模板扫描
- **sqlmap** SQL 注入探测(配 `?case_no=*`)
- **CSRF / SSRF** 手工构造

### 5.2 必跑场景

| # | 场景 | 期望 |
|---|---|---|
| 1 | 创建 user_A 与 user_B,拿 user_B 的 case_no 在 user_A session 下 GET / PATCH / DELETE | 403 |
| 2 | 改 cookie `yq_session` 的 `role` 字段(JWT payload 注入) | 401(签名校验失败) |
| 3 | JWT alg=none 重签 | 401 |
| 4 | OSS STS 签发后改 `key` 上传到他人目录 | 403(policy prefix 强制) |
| 5 | 普通会员调 `/api/reports/:id` → 响应 JSON 不应有 `priceRange/recyclePrice/...` | JSON 不含 |
| 6 | 无 session GET `/api/customer-brief/:id` | 401 |
| 7 | 注入 SQL:`?case_no=' OR 1=1--` / `?status='; DROP TABLE cases;--` | 400(参数校验)或 403,**不执行** |
| 8 | XSS:在 `cases.title` 提交 `<script>alert(1)</script>`,管理后台渲染 | DOM 中转义,不执行 |
| 9 | CSRF:从第三方域跨域 POST `/admin/export/cases` | 失败(SameSite=Lax + Origin 校验) |
| 10 | SSRF:`POST /api/uploads/by-url`(若存在)指向 `127.0.0.1:5432` / `169.254.169.254` | 拒绝(M4 不提供 by-url 上传,但若加要堵) |
| 11 | 短信:60s 内连发 100 次 | 第 2 次起 429 |
| 12 | OCR 同 case 1h 内调 100 次 | 第 6 次起 429 |
| 13 | 暴破登录:同 IP 100 次错码 | 锁号 + IP 拉黑 |
| 14 | 上传 50 MB 图片(超 max-size) | 阿里云拒收 |
| 15 | 上传 `.html`/`.svg` 当 jewelry 图(MIME 欺骗) | 后端 MIME 白名单拒收 |
| 16 | 报告 PDF 越权:user_A 拿 user_B 的 `report_id` 下载 | 403 |
| 17 | 管理员看原图 5 次 → 查 `admin_operation_logs` 有 5 条 | 行数对得上 |
| 18 | 管理员账号被禁(`status=disabled`),session 还在 | 下次请求 → 401(`get_current_user` 重查 status) |
| 19 | 超管被禁,super 路径访问 | 401 |
| 20 | 跨云 Azure 故意构造 timeout(防火墙 drop):API 应 500 + `ai_call_logs.status='timeout'`,不卡死 | 60s 内响应 |

### 5.3 报告产出

- 每次渗透出 `pentest-report-YYYY-MM-DD.md`,P0 / P1 漏洞**修完前不上 production**
- 报告归档至 `docs/audit/` 目录(私库)

---

## 6. 应急响应清单

> 真出事时按以下步骤;不要慌,先**止损 → 评估 → 沟通 → 复盘**。

### 6.1 凭据泄露(secret 进了 git / 公开)

1. **立即** revoke:Azure key / Aliyun AK/SK / DB 密码 / JWT_SECRET 全换
2. **立即** 撤销所有 user session(`FLUSHDB` Redis JWT 黑名单不够,直接换 JWT_SECRET 让所有 token 失效)
3. 查 `admin_operation_logs` 与 `ai_call_logs` 看是否有异常调用
4. 通知业务方与法务,评估披露义务
5. 复盘 `gitleaks` 为何漏(CI 失效?新文件白名单?)

### 6.2 SQL 注入告警

1. WAF 临时拉黑攻击 IP / Pattern
2. 查应用日志看是否真有数据返回
3. 复查 D-01 / D-02,有问题代码立即下线
4. 跑 sqlmap 自测是否还能复现

### 6.3 OSS 公开数据泄露

1. **立即**改 Bucket ACL 回 private
2. 列举近 24h `case_files` 新增,标记可能被访问
3. 联系阿里云客服拉访问日志
4. 通知受影响用户(GDPR / 《个保法》要求)
5. 排查 RL-03 在哪一步被绕过

### 6.4 AI 调用异常激增 / 配额耗尽

1. 临时把 `quota_service` 全局上限拉低(env hot reload)
2. 查 `ai_call_logs` 锁定来源用户 / IP
3. 评估是否被脚本攻击;封号 + 退款
4. Azure quota 申请提速(若是合法增长)

### 6.5 管理员账号被撞库

1. **立即**禁用涉事账号(`users.status='disabled'`)
2. 强制所有管理员密码重置 + 2FA(P1)
3. 查 `admin_operation_logs` 看 24h 内所有操作
4. 通知超管 + 业务方

---

## 7. 未决项(与 tracker §二 对齐)

详见 [docs/discussions/M4-backend-rollout-tracker.md §二](./discussions/M4-backend-rollout-tracker.md):

- [ ] §2.4 阿里云 KMS 接入(F-04)依赖业务方账号 ownership
- [ ] §2.4 ICP 备案进度直接影响 I-01 / I-02(无备案不能开 HTTPS 正式域)
- [ ] 2FA 管理员登录(6.5 应急响应想要,但 M4 范围未含)— 推 P1
- [ ] WAF 是否上(I-06)— 阿里云 WAF 实例费,业务方决策
- [ ] 渗透测试供应商选定(§5 必须外部跑)

---

## 维护规则

1. **每条 ID 永远不复用**;弃用项保留 ID 标 `[已废弃]`
2. 每次发现新红线 → 优先升 §1 总览表;次要项进 §3 对应类目
3. 自动化测试新增/废弃 → §4 映射表同步
4. M5 上线前必须**全部通过**:§1 红线 8 条 100%、§3 P0 项 100%、§3 P1 项 ≥ 90%
5. 季度 review 一次,过期项整体过一遍
6. **violation 与 fix 都进 commit message**,搜索方便事后追溯
