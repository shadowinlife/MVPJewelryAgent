# M4 后端铺设 — 讨论进度跟踪

> 临时讨论区。用来跟踪**已有结论**与**尚未讨论**的部分,避免重复对齐。
> 起始:2026-05-22 / 最后更新:2026-05-24
> 父文档:[Backend-Architecture_v0.1.md](../Backend-Architecture_v0.1.md)、[roadmap.md](../roadmap.md)、[milestones/M4-real-backend.md](../milestones/M4-real-backend.md)

---

## 一、已有结论(2026-05-22 拍板)

### 1.1 后端核心选型(对应 Backend-Architecture §16)

| # | 议题 | 决议 |
|---|---|---|
| 0 | 后端语言 / 框架 | ✅ FastAPI(Python 3.12) |
| 1 | 异步队列 | ✅ Arq(排除 Celery / BullMQ) |
| 2 | 微信登录 | ✅ 推 P1;M4 只做手机号 + 邮箱 + 密码 |
| 3 | OSS 上传通道 | ✅ 阿里云 OSS + STS 直传(文件不过后端) |
| 4 | 短信服务商 | ✅ 阿里云短信 |
| 5 | LLM 提供方 | ✅ **Azure OpenAI Service @ HongKong**(唯一);排除豆包 / 通义千问 |
| 5a | M4 AI 落地深度 | ✅ 只预留 `LLMClient` 抽象接口 + prompt/schema/配额脚手架;真接入由 AI 工程那一脚承接 |
| 6 | RAG / pgvector | ✅ M4 装扩展 + 写入 embedding,**召回开关默认关** |
| 7 | i18n 错误码 | ✅ 推 P1(本期 `error` 用中文短句) |
| 8 | Postgres | ✅ 阿里云 RDS PostgreSQL 16(原生 pgvector) |
| 9 | LangChain / LlamaIndex / DSPy | ✅ 不引入 |

### 1.2 跨云部署拓扑(Backend-Architecture §16.1 / §9.7)

- **主体业务后端**:阿里云(ECS + RDS + Tair/Redis + OSS + OCR + 短信)
- **AI**:Azure OpenAI Service @ HongKong,后端跨云**公网直连**
- M4 **不**引入 API Gateway / VPN 专线;`timeout=60s` + `tenacity` 重试 + `ai_call_logs.latency_ms` 兜底
- 排除项(不要回推):OpenAI 平台直连 / 把后端整体搬到 Azure / 国内 LLM 备份

### 1.3 §17 后续文档进度(5/6)

| 文档 | 状态 | 链接 |
|---|---|---|
| `skills/backend-engineer.md` | 🟢 已产出 | [skills/backend-engineer.md](../../skills/backend-engineer.md) |
| `skills/ai-integration-engineer.md` | 🟢 已产出 | [skills/ai-integration-engineer.md](../../skills/ai-integration-engineer.md) |
| `Backend-Database-Schema_v0.1.md` | 🟢 已产出 (2026-05-22) | [Backend-Database-Schema_v0.1.md](../Backend-Database-Schema_v0.1.md) |
| `Backend-Security-Checklist_v0.1.md` | 🟢 已产出 (2026-05-22) | [Backend-Security-Checklist_v0.1.md](../Backend-Security-Checklist_v0.1.md) |
| `Backend-Deployment-Guide_v0.1.md` | 🟢 已产出 (2026-05-23) | [Backend-Deployment-Guide_v0.1.md](../Backend-Deployment-Guide_v0.1.md) |
| `Backend-API-Spec_v0.1.yaml` | 🟡 推后 | 待 FastAPI 骨架起来后从 `/openapi.json` 自动导出 |

### 1.4 M4 实施进度(2026-05-24 更新)

实施侧迁移到 [milestones/M4-real-backend.md](../milestones/M4-real-backend.md);本节只留**阶段性结论**,细任务别复制。

| Stage | 范围 | 状态 | 完成日 |
|---|---|---|---|
| **Stage 1: Foundation** | FastAPI 骨架 + `/health(self)` + envelope / request-id 中间件 + Settings + structlog + Dockerfile + pytest 骨架(10 用例) | 🟢 完成 | 2026-05-24 |
| **Stage 2: Persistence** | 13 张 ORM + Alembic 初始迁移 + testcontainers fixture;`/health` 扩 `checks.db` | ⚪ 未启动 | — |
| **Stage 3: Tier Schemas** | 7 个 tier Pydantic schema + 服务端字段裁剪覆盖详情/客户简洁版 | ⚪ 未启动 | — |
| **Stage 4: API + Integrations** | auth/cases/reports/files/ocr/memberships 路由 + JWT + RBAC + `LLMClient` + OSS/OCR/短信 client | ⚪ 未启动 | — |

**Stage 1 落地附带的工程约定**(本会话引入,跨会话生效):

- AGENT.md 新增「代码规范 / 注释即文档(Code-as-Doc)」:`class` / `def` / 关键业务逻辑 / 关键变量 必须中文 docstring + WHY 注释。**覆盖 Claude Code 默认"少注释"规则**,Stage 2~4 全部继承。
- 信封 `{ok, data, error, source}` 四字段对齐前端 TS,`extra="forbid"` 锁死;失败信封**禁泄漏** `code` / `requestId` / 内部异常类型(测试守住)。
- 中间件挂载顺序固定:外层 `ErrorHandlerMiddleware`(兜底)/ 内层 `RequestIdMiddleware`(给错误日志带 request_id)。Stage 2~4 加新中间件需在 `app/main.py` 注释清楚相对位置。

下一步候选(等业务方拍板):

- **Stage 2 启动**(工程方独立可推,不依赖物料)— 推荐
- **等物料解锁后跨 Stage 推进** — 见 §2.4
- **回头铺 M3**

---

## 二、尚未讨论的部分(等业务方 / 待对齐)

### 2.1 ~~§17 文档进度 5/6 — 进入实施前的下一步~~(2026-05-24 已结案,迁移到 §1.4)

~~A + B 并行~~ 已拍板 + 已执行:
- ✅ **B 路径 Stage 1** 完成于 2026-05-24,产物详见 [milestones/M4-real-backend.md](../milestones/M4-real-backend.md);后续 Stage 2~4 在 §1.4 跟踪。
- 🟡 **A 路径物料收集** 仍在业务方手里,跟踪表见 §2.4 / [M4-materials-acquisition-workpack.md](./M4-materials-acquisition-workpack.md)。
- ⚪ **C 路径** M3 未启动,等业务方决定是否插队。

### 2.2 `Backend-API-Spec_v0.1.yaml` 的解锁触发

当前推后理由:手写 OpenAPI YAML 与 §6 完全重复,信息密度低。
解锁触发条件(任一):
- FastAPI 骨架代码已落,可跑 `python -c "import app.main; print(app.main.app.openapi())"` 导出
- 业务方对外**提前**披露 API 给第三方(如客户的 SaaS / 经销商) — 这种情况需要手写 YAML

### 2.3 M3 vs M4 路标顺序(roadmap 一直挂着)

| 路径 | 含义 | 适合时机 |
|---|---|---|
| **先 M3** | 把后台 11 页面 mock 完整,再一起接真后端 | 业务方需要"全功能演示"路演 |
| **先 M4** | 现在就铺真后端,后台页面以后再补 | 业务方需要数据真存进去 / 真鉴定真出报告 |

未决。

### 2.4 M4 实施前还需要业务方提供的物料

🟡 **2026-05-23 已展开为工作包**:[M4-materials-acquisition-workpack.md](./M4-materials-acquisition-workpack.md)(12 项执行卡 + 关键路径 + RAM/KMS/ICP/短信模板)。每周一同步状态;阻塞抬到本节。

- [ ] M-01 阿里云主账号 access(项目方负责人)
- [ ] M-02 工程师子账号 + RAM 策略(ops)
- [ ] M-03 Azure 订阅 + OpenAI 资源 ownership(项目方 + AI 工程接口人)
- [ ] M-04 域名 + ICP 备案 ⚠️ **关键路径最长 7-20 天**(负责人 + 法务)
- [ ] M-05 阿里云短信签名审核(ops)
- [ ] M-06 短信模板审核(ops)
- [ ] M-07 OSS Bucket 创建(ops + tech lead)
- [ ] M-08 私调 Azure deployment 名 — M4 不卡,用 `gpt-4o-mini` 顶
- [ ] M-09 KMS CMK + Secret 入库(ops + DevOps)
- [ ] M-10 真实玉石 / 珠宝样本 — 滚动收集,不卡上线但卡 AI 评测
- [ ] M-11 监控告警通道(ops)
- [ ] M-12 跳板机 SSH 公钥白名单(tech lead)

### 2.5 AI 工程那一脚的接手时机

`skills/ai-integration-engineer.md` 已就位,但**何时切**还没说:
- 选项 1:M4 后端实施完成、`LLMClient` stub 已落,再由 AI 工程进场填实
- 选项 2:M4 与 AI 并行(各自一个分支),最后合
- 选项 3:同一个代理身份切换(同一个人 / 同一个 AI 代理串行扮演两个角色)

未决。

### 2.6 M4 与前端的合流方式

Backend-Architecture §14 已给方案(双写期 → 关 mock route → 删 mock json),但**双写期的具体灰度策略**(按用户 / 按接口 / 按比例)未拍板。

---

## 三、参考索引(避免重读长文档)

- 已拍板决议表:[Backend-Architecture_v0.1.md §16](../Backend-Architecture_v0.1.md)
- 跨云拓扑速记:[Backend-Architecture_v0.1.md §16.1 + §9.7](../Backend-Architecture_v0.1.md)
- 后端目录结构:[Backend-Architecture_v0.1.md §4.1](../Backend-Architecture_v0.1.md)
- `LLMClient` Protocol 与 Azure stub:[Backend-Architecture_v0.1.md §9.3](../Backend-Architecture_v0.1.md)
- M4 验收 Checklist:[Backend-Architecture_v0.1.md §15](../Backend-Architecture_v0.1.md)
- 跨会话长期记忆:`.claude/projects/-Users-mgong-PycharmProjects-ZhuBaoTest/memory/`
  - `yaoqi-backend-stack` / `yaoqi-deployment-topology` / `yaoqi-membership-tiers`

---

## 维护规则

1. **新结论拍板**:从 §二 移到 §一,带日期(`(2026-MM-DD 拍板)`)
2. **新开放议题**:加进 §二,标明等谁、为什么没决
3. **文档关闭**:M4 实施开工后,可整体迁到 `docs/milestones/M4-real-backend.md`,本文件归档或删除
4. 不要在这里复制 Backend-Architecture 的细节 — 只放**决策**与**未决项**,长文继续在 §三 链回去
