# 曜齐 YAOQI 玉石珠宝鉴定估价助手 — Roadmap

> 总览文件,按 AGENT.md §2 工作流维护。每个路标(里程碑)对应 [`milestones/`](./milestones/) 下的独立文件。
> 最后更新:2026-06-01(M4 Stage 4 启动 — LLM 多 Provider 抽象落地 + DashScope qwen3.7-max 连通 + admin 配置页)

## 项目背景

定位:**奢侈品下游服务商**,服务范围聚焦 **玉石 + 珠宝**(明确不含箱包/手表/贵金属/古董字画),为客户的"购买、质量鉴定、定价"三件事提供 AI 辅助。

参考文档:

| 文档 | 作用 |
|------|------|
| [Product-Spec_v0.4.md](./Product-Spec_v0.4.md) | 产品边界、MVP Level 划分、数据资产策略 |
| [UI-Spec_v0.3.1.md](./UI-Spec_v0.3.1.md) | UI 规范(配色 / 字体 / 21 个页面 / 验收) |
| [Technical-Spec_v0.1.md](./Technical-Spec_v0.1.md) | 技术栈、API、数据库 Schema、OSS 安全 |

技术栈(本轮拍板):

- **前端**:Next.js 15 App Router + TypeScript + Tailwind CSS + shadcn/ui;M4 之前 Mock 数据走 Next.js Route Handlers
- **后端**(2026-05-22 拍板):FastAPI(Python 3.12)+ 阿里云 RDS PostgreSQL 16(原生 pgvector)+ Arq 异步队列;详见 [Backend-Architecture_v0.1.md](./Backend-Architecture_v0.1.md)
- **AI / LLM**:prod = Azure OpenAI @ HK;dev/staging = **DashScope qwen3.7-max**(多模态,支持图片);后端 `LLMClient` Protocol 动态切换,admin 页面配置
- **存储 / 短信 / OCR**:阿里云 OSS(STS 预签名直传)+ 阿里云短信 + 阿里云 OCR

---

## 里程碑总览

| ID | 名称 | 状态 | MVP Level | 范围 | 链接 |
|----|------|------|-----------|------|------|
| M1 | Foundation | 🟢 已完成 2026-05-22 | Level 1 → 2 准备 | 项目骨架 + 设计系统 + 共享组件 + mock 数据契约 | [M1-foundation.md](./milestones/M1-foundation.md) |
| M2 | User Pages | 🟢 已完成 2026-05-22 | Level 2 | 用户端 10 个页面,登录 → 报告全流程可点击 | [M2-user-pages.md](./milestones/M2-user-pages.md) |
| M3 | Admin Pages | ⚪ 未开始 | Level 2 | 管理后台 11 个页面 | 📝 **路标文件待创建** `M3-admin-pages.md`(业务方插队前 1h 内补写)|
| M4 | Real Backend | 🟡 进行中 3/4 Stage | Level 3 | 接真后端 / 数据库 / OSS / OCR / AI | [M4-real-backend.md](./milestones/M4-real-backend.md) |
| M5 | Pre-public Beta | ⚪ 未开始 | Level 4 | 域名 / HTTPS / 协议 / 备份 / 安全验收 | (待规划)|

状态图例:🟢 已完成 / 🟡 进行中 / ⚪ 未开始 / 🔴 阻塞

**M4 Stage 进度**(详细任务清单见 [M4-real-backend.md](./milestones/M4-real-backend.md)):

| Stage | 范围 | 状态 | 阻塞依赖 |
|---|---|---|---|
| Stage 1: Foundation | FastAPI 骨架 + `/health(self)` + 信封 + Request-ID + Dockerfile + pytest | 🟢 完成 2026-05-24 | — |
| Stage 2: Persistence | 13 ORM + Alembic 0001 + testcontainers + `/health.db` | 🟢 完成 2026-05-24 | — |
| Stage 3: Tier Schemas | 7 tier Pydantic + `crop_report_for_user` + 8 RBAC 红线锁定(54 测试全绿) | 🟢 完成 2026-05-26 | — |
| Stage 4: API + Integrations | 路由 + JWT + RBAC + LLMClient + OSS/OCR/短信 client + Seed | 🟡 进行中 | LLM 子系统 ✅;Auth / Cases / OSS / SMS 待推 |

---

## 关键路径与外部依赖(非编码,独立时间线)

> **写在这里的理由**:这些项 lead time 长、无法靠编码进度压缩,编码再快也卡在它们上线;必须与编码并行触发,不能等 Stage 4 写完才动。
>
> **2026-05-26 重要变更**:**M-04 域名 + ICP 备案已废弃**。决议"网站前端部署在香港节点(非境内服务器),后端 + DB + OSS 仍在阿里云华东";前端在境外节点无需工信部 ICP。原 7-20 天关键路径**直接消除**,替换为 **M-13 HK 前端节点 + 域名 DNS 接管**(1-3 天)。详见 [workpack §M-13](./discussions/M4-materials-acquisition-workpack.md)。

| 物料 | Owner | Lead Time | 状态 | 失败影响 |
|---|---|---|---|---|
| ~~**M-04 域名 + ICP 备案**~~ | ~~项目方负责人 + 法务~~ | ~~7–20 天~~ | 🚫 已废弃 2026-05-26 | — |
| **M-03 Azure 订阅 + OpenAI 准入** ⚠️ **新关键路径最长** | 项目方负责人 + AI 工程 | **7–14 天** | ⚪ | AI 链路无法接入(Stage 4 LLMClient 只能 stub) |
| M-13 HK 前端节点 + 域名 DNS 接管(替代 M-04)| 项目方负责人 + tech lead | 1–3 天 | ⚪ | 前端无对外访问入口;CORS / cookie 跨域细节 Stage 4 需联动 |
| M-01 阿里云主账号 + 实名 + 充值 | 项目方负责人 | 1–3 天 | 🟢 完成 2026-06-01 | — |
| M-05 + M-06 短信签名 + 模板 | 项目方 ops | 1–3 天 / 项 | ⚪ | 登录验证码下不去(MVP 核心断流)|
| M-07 OSS Bucket(private + SSE-KMS) | 项目方 ops + tech lead | 0.5 天(待 M-01) | ⚪ | OSS 直传无法启用 |
| M-09 KMS CMK + Secret 入库 | 项目方 ops + DevOps | 1 天(待 M-01) | ⚪ | Secret 只能裸写 `.env`,违反 [Security-Checklist](./Backend-Security-Checklist_v0.1.md) |

完整 12 项执行卡(含 RAM 策略 JSON / 短信文案 / HK 前端选型):[M4-materials-acquisition-workpack.md](./discussions/M4-materials-acquisition-workpack.md);§5 原 ICP 材料清单保留为历史参考,不再走流程。

**行动闸口**:**M-03 Azure OpenAI 准入**取代原 M-04 成为新最长 lead time(7-14 天),**本周必须启动**(2026-05-25 ~ 2026-05-31 内提交 Limited Access Form)。M-13 HK 节点选型(Vercel HK / 阿里云 HK / Cloudflare)1-3 天可定,等 Stage 4 前端集成时联动。

---

## 当前 Sprint 焦点

**进度速览**:M4 Stage 4 已启动(2026-06-01)。LLM 多 Provider 抽象 + Admin 配置页完成,DashScope qwen3.7-max 端到端连通验证通过。累计 51 测试全绿(Stage 1×10 + Stage 2×17 + Stage 3×27 − Docker 依赖测试;新增 LLM 7 测试);ruff/mypy --strict/tsc 全干净。

**Stage 4 已完成子系统**:
- ✅ `LLMClient` Protocol + DashScope/Azure 双 adapter + factory + Fernet 加密
- ✅ Admin 配置页(后端 API + 前端 form)— 支持动态切换 Provider / Key / Endpoint / Model
- ✅ DashScope qwen3.7-max 连通验证(多模态,支持图片输入)
- ✅ M-01 阿里云主账号已完成

### 主线焦点:**Stage 4 继续推进 — 核心业务链路**

LLM 已通,下一步是让"上传珠宝照片 → AI 鉴定 → 生成报告"完整跑通。推荐顺序:

| 优先级 | 子系统 | 依赖 | 产出 |
|---|---|---|---|
| **P0** | Auth(JWT 登录/注册)| 无外部依赖 | `POST /auth/login` + `POST /auth/register` + JWT middleware + RBAC deps |
| **P1** | Cases CRUD + Files 路由 | Auth | `POST /cases` + `PUT /cases/:id` + file 关联 |
| **P2** | AI 鉴定业务链路 | LLMClient ✅ + Cases | prompt 模板 + 图片 → qwen3.7-max 多模态分析 → InternalReport → crop |
| **P3** | OSS 直传(STS 预签名)| M-07 Bucket | 前端直传 + callback 确认 |
| **P4** | 短信验证码 | M-05/M-06 | 登录流程可选增强 |

### 并行轨道(非编码)

1. **M-03 Azure OpenAI 准入** — 7-14 天 lead time;不阻塞开发(DashScope 替代),但 prod 上线前必须到位
2. **M-07 OSS Bucket 创建** — M-01 已通,可立即操作(ops)
3. **M-05/M-06 短信签名 + 模板审核** — M-01 已通,可并行提交
4. **M-09 KMS Secret 入库** — 依赖 M-01 ✅,可操作
5. **M-13 HK 前端节点选型** — Stage 4 前端对接时联动
6. **§2.6 前端双写期灰度策略** — 不阻塞后端开发,Stage 4 收尾时再定

### 已解除的阻塞

- ~~§2.5 AI 工程接手时机~~ — 事实上已 bypass:LLMClient 直接真接入 DashScope,非 stub;后续 prompt 编排与路由开发在同一上下文进行
- ~~M-01 阿里云主账号~~ — ✅ 已完成
- ~~M-04 ICP 备案~~ — 🚫 已废弃 2026-05-26

讨论决策日志详见 [discussions/M4-backend-rollout-tracker.md](./discussions/M4-backend-rollout-tracker.md)。

---

## 待业务方决策的开放问题

> 完整未决项跟踪在 [tracker §二](./discussions/M4-backend-rollout-tracker.md);本节只挂**会卡住下一 Stage 启动的"高优"项**,拍板后从这里移走。

**🟢 已解除**(2026-06-01):

- ~~**§2.5 AI 工程接手时机**~~ — LLMClient 已真接入 DashScope(非 stub),不再阻塞

**🟡 不阻塞开发但影响收尾**:

- **§2.6 前端双写期灰度策略** — Stage 4 收尾时 mock route 关停顺序(按用户 / 按接口 / 按比例),影响前端切换风险

**🟡 滚动收集 / 不卡 Stage 但卡上线**:

- 真实玉石 / 珠宝样本(目标 20+ 套含证书) — 不卡 M4 上线,卡 AI 评测,见 [M-10](./discussions/M4-materials-acquisition-workpack.md)
- 业务方是否选择 M3 插队 — 影响 Sprint 排程,见 tracker §2.3

**🟢 已拍板归档**(留作历史检索,后续直接擦除):

- ~~真实品牌 Logo / VI 手册~~ → 2026-05-22:暂无,`BrandLogo` 文字占位
- ~~5 档会员等级解锁映射~~ → 2026-05-22:差异核心为月度 Token 配额(2 万 → 200 万)
- ~~后端语言选 NestJS / Next.js Server Actions / FastAPI~~ → 2026-05-22:**FastAPI**(Python 3.12)
- ~~OSS 上传走中转还是预签名直传~~ → 2026-05-22:**STS 预签名直传**(文件不过后端)

---

## 工作流约定(摘自 AGENT.md)

1. 先制定计划,有争议点 Human-in-loop 讨论清楚后再开发
2. 每个里程碑独立文件跟踪进度
3. 每完成一个任务,在路标文件中记录完成内容
4. 每完成一个路标,更新本文件的状态
5. 及时补充测试和执行 git commit,每个 commit 包含一个完整功能点
6. 及时更新 `docs/` 下的相关文档
7. **每周一回看「关键路径与外部依赖」表**,任何 ⚪ → 🟡 → 🟢 状态推进及时同步;阻塞项升级到「待业务方决策」🔴 区
8. **"待业务方决策"🔴 区拍板后**立即从本文件移走,只在 🟢 已归档区留一行历史(保留 ≤ 90 天,过期擦除)
