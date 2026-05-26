# 曜齐 YAOQI 玉石珠宝鉴定估价助手 — Roadmap

> 总览文件,按 AGENT.md §2 工作流维护。每个路标(里程碑)对应 [`milestones/`](./milestones/) 下的独立文件。
> 最后更新:2026-05-26(M4 Stage 3 落地 — 7 tier Pydantic + 8 红线锁定;Stage 4 等物料 + AI 工程接手时机拍板)

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
- **AI / LLM**:Azure OpenAI Service @ HongKong **唯一通道**,跨云公网直连(不引 API Gateway / VPN)
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
| Stage 4: API + Integrations | 路由 + JWT + RBAC + LLMClient + OSS/OCR/短信 client + Seed | ⚪ 未启动 | ⚠️ 受物料 M-01/M-03/M-05/M-06/M-07/M-09 阻塞(见 §关键路径)+ §2.5 AI 接手时机 + §2.6 灰度策略待拍板 |

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
| M-01 阿里云主账号 + 实名 + 充值 | 项目方负责人 | 1–3 天 | ⚪ | 一切阿里云资源无法创建 |
| M-05 + M-06 短信签名 + 模板 | 项目方 ops | 1–3 天 / 项 | ⚪ | 登录验证码下不去(MVP 核心断流)|
| M-07 OSS Bucket(private + SSE-KMS) | 项目方 ops + tech lead | 0.5 天(待 M-01) | ⚪ | OSS 直传无法启用 |
| M-09 KMS CMK + Secret 入库 | 项目方 ops + DevOps | 1 天(待 M-01) | ⚪ | Secret 只能裸写 `.env`,违反 [Security-Checklist](./Backend-Security-Checklist_v0.1.md) |

完整 12 项执行卡(含 RAM 策略 JSON / 短信文案 / HK 前端选型):[M4-materials-acquisition-workpack.md](./discussions/M4-materials-acquisition-workpack.md);§5 原 ICP 材料清单保留为历史参考,不再走流程。

**行动闸口**:**M-03 Azure OpenAI 准入**取代原 M-04 成为新最长 lead time(7-14 天),**本周必须启动**(2026-05-25 ~ 2026-05-31 内提交 Limited Access Form)。M-13 HK 节点选型(Vercel HK / 阿里云 HK / Cloudflare)1-3 天可定,等 Stage 4 前端集成时联动。

---

## 当前 Sprint 焦点

**进度速览**:M4 Stage 1+2+3 已完成(2026-05-24 ~ 2026-05-26)。Stage 3 落地后 54 测试全绿(Stage 1 × 10 + Stage 2 × 17 + Stage 3 × 27),ruff/mypy --strict 干净;8 条 RBAC 数据红线由 Pydantic `extra="forbid"` 物理兜底 + `crop_report_for_user` 唯一裁剪入口锁定。Stage 详细任务清单见 [M4-real-backend.md](./milestones/M4-real-backend.md);跨会话工程约定(注释即文档 / 不引 psycopg / `clock_timestamp()` / ReportAdmin 独立 export 等)见 [memory 索引](../.claude/projects/-Users-mgong-PycharmProjects-ZhuBaoTest/memory/MEMORY.md) 与 [tracker §1.4](./discussions/M4-backend-rollout-tracker.md)。

**M4 §17 前置文档进度 5/6**(`Backend-API-Spec_v0.1.yaml` 推后到 Stage 4 后由 `/openapi.json` 自动导出):
[skills/backend-engineer.md](../skills/backend-engineer.md) · [skills/ai-integration-engineer.md](../skills/ai-integration-engineer.md) · [Backend-Architecture](./Backend-Architecture_v0.1.md) · [Backend-Database-Schema](./Backend-Database-Schema_v0.1.md) · [Backend-Security-Checklist](./Backend-Security-Checklist_v0.1.md) · [Backend-Deployment-Guide](./Backend-Deployment-Guide_v0.1.md) — 全 🟢 已产出。

### 主线焦点:**Stage 4 启动前置 — 物料解锁 + 2 个拍板**

工程侧 Stage 3 收尾后**唯一可继续推进**的事不是编码,而是**等业务方决策 + 物料到位**。Stage 4 路由代码本身可以独立写出 stub,但 OSS / SMS / Azure 接入不能 `NotImplementedError` 就交付。

**Stage 4 启动闸口**(任一不达成则 Stage 4 不开):

1. 🔴 **§2.5 AI 工程接手时机拍板** — 决定 `LLMClient` 落地深度(stub vs 真接入),工作量 ±40%(3 选项见 tracker)
2. 🔴 **§2.6 前端双写期灰度策略拍板** — 决定 mock route 关停顺序(按用户 / 按接口 / 按比例)
3. 🟡 至少 **M-01 + M-09** 解锁(阿里云主账号 + KMS Secret 入库)— 让 Settings 能从 KMS 读 OSS / SMS 密钥而非裸 `.env`

### 并行轨道(非编码,**必须本周推进**)

1. ~~**M-04 ICP 备案**~~ **已废弃 2026-05-26** — 改走 HK 前端节点(M-13),无 ICP 要求
2. **M-03 Azure OpenAI 准入(新最长关键路径)** — 项目方负责人本周内提交 Limited Access Form,7-14 天 lead time(否则 Stage 4 LLM 链路只能 stub)
3. **拍板 §2.5 AI 工程接手时机** — 决定 Stage 4 `LLMClient` 做 stub 还是真接入(工作量 ±40%)
4. **拍板 §2.6 前端双写期灰度策略** — 决定 Stage 4 收尾时 mock route 关停顺序
5. **M-13 HK 前端节点选型**(Vercel HK / 阿里云 HK / Cloudflare)— Stage 4 启动前定型即可,1-3 天 lead time
6. **补写 `docs/milestones/M3-admin-pages.md` 占位**(1h)— 业务方临时插队 M3 时不至于挂空文件

### 暂不启动(原因)

- ❌ **Stage 4** — 12 项物料**仍全 ⚪**,且 §2.5 / §2.6 未拍板;现在写路由 stub 会浪费 30~40% 返工
- ❌ **M3 Admin Pages** — 业务 ROI 是"路演价值"而非"后端真数据",优先级低于 Stage 4 启动闸口;且 milestone 文件未建

### 工程侧若仍需推进(选填,低优)

可考虑的"不阻塞、不返工"小项:

- 把 27 Stage 3 测试中的 inline `_make_internal_full()` 工厂转成 `tests/factories/` 抽象(Stage 4 写 service 测试时收益更大)
- 给 `app/schemas/__init__.py` 加 docstring 总览导出树
- 在 `backend/README.md` 加 Stage 3 章节(crop_report_for_user 用法 + 8 条红线对照表)

讨论决策日志详见 [discussions/M4-backend-rollout-tracker.md](./discussions/M4-backend-rollout-tracker.md)。

---

## 待业务方决策的开放问题

> 完整未决项跟踪在 [tracker §二](./discussions/M4-backend-rollout-tracker.md);本节只挂**会卡住下一 Stage 启动的"高优"项**,拍板后从这里移走。

**🔴 卡住 Stage 4 启动的强制 closure 项**(必须在 Stage 3 收尾前定):

- **§2.5 AI 工程接手时机** — 决定 Stage 4 `LLMClient` 落地深度(stub vs 真接入),工作量 ±40%。3 选项见 tracker。
- **§2.6 前端双写期灰度策略** — Stage 4 收尾时 mock route 关停顺序(按用户 / 按接口 / 按比例),影响切换风险。

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
