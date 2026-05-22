# 曜齐 YAOQI 玉石珠宝鉴定估价助手 — Roadmap

> 总览文件,按 AGENT.md §2 工作流维护。每个路标(里程碑)对应 [`milestones/`](./milestones/) 下的独立文件。

## 项目背景

定位:**奢侈品下游服务商**,服务范围聚焦 **玉石 + 珠宝**(明确不含箱包/手表/贵金属/古董字画),为客户的"购买、质量鉴定、定价"三件事提供 AI 辅助。

参考文档:

| 文档 | 作用 |
|------|------|
| [Product-Spec_v0.4.md](./Product-Spec_v0.4.md) | 产品边界、MVP Level 划分、数据资产策略 |
| [UI-Spec_v0.3.1.md](./UI-Spec_v0.3.1.md) | UI 规范(配色 / 字体 / 21 个页面 / 验收) |
| [Technical-Spec_v0.1.md](./Technical-Spec_v0.1.md) | 技术栈、API、数据库 Schema、OSS 安全 |

技术栈(本轮拍板):**Next.js 15 App Router + TypeScript + Tailwind CSS + shadcn/ui**,Mock 数据通过 Next.js Route Handlers 返回。

---

## 里程碑总览

| ID | 名称 | 状态 | MVP Level | 范围 | 链接 |
|----|------|------|-----------|------|------|
| M1 | Foundation | 🟢 已完成 (2026-05-22) | Level 1 → 2 准备 | 项目骨架 + 设计系统 + 共享组件 + mock 数据契约 | [M1-foundation.md](./milestones/M1-foundation.md) |
| M2 | User Pages | 🟢 已完成 (2026-05-22) | Level 2 | 用户端 10 个页面,登录 → 报告全流程可点击 | [M2-user-pages.md](./milestones/M2-user-pages.md) |
| M3 | Admin Pages | ⚪ 未开始 | Level 2 | 管理后台 11 个页面 | [M3-admin-pages.md](./milestones/M3-admin-pages.md)(待创建)|
| M4 | Real Backend | ⚪ 未开始 | Level 3 | 接真后端 / 数据库 / OSS / OCR / AI | (待规划)|
| M5 | Pre-public Beta | ⚪ 未开始 | Level 4 | 域名 / HTTPS / 协议 / 备份 / 安全验收 | (待规划)|

状态图例:🟢 已完成 / 🟡 进行中 / ⚪ 未开始 / 🔴 阻塞

---

## 当前 Sprint 焦点

**M2 已完成 (2026-05-22)**:用户端 10 个页面跑通 — 登录 → 工作台 → 案例库 → 5 步新建 → OCR → 案例详情(含会员裁剪) → 客户简洁版 → 我的 / 会员。`curl` 全绿,响应式断点待人工 375 / 768 / 1024 视觉走查。

**下一步候选**:M3 管理后台 11 页(需先创建 `M3-admin-pages.md` 路标),或进入 M4 接真后端(需先决定后端选型)。等待业务方拍板。

---

## 待业务方决策的开放问题

参见 [smooth-juggling-thimble.md 计划文件 "待解决的开放问题" 节](../../../.claude/plans/smooth-juggling-thimble.md) — 不在本仓库内,需要时由 AI 代理回读。

主要待确认项:

- ~~真实品牌 Logo / VI 手册是否存在?~~ → 2026-05-22 拍板:暂无,`BrandLogo` 占位
- 真实案例样本(玉石/珠宝图片 + 证书扫描件 + 报告文本)是否能提供?
- ~~5 档会员等级解锁映射是否符合商业策略?~~ → 2026-05-22 拍板:差异核心为月度 Token 配额(2 万 → 200 万)
- 后端正式接入时选 NestJS / Next.js Server Actions / FastAPI?
- OSS 上传走中转还是预签名直传?

---

## 工作流约定(摘自 AGENT.md)

1. 先制定计划,有争议点 Human-in-loop 讨论清楚后再开发
2. 每个里程碑独立文件跟踪进度
3. 每完成一个任务,在路标文件中记录完成内容
4. 每完成一个路标,更新本文件的状态
5. 及时补充测试和执行 git commit,每个 commit 包含一个完整功能点
6. 及时更新 `docs/` 下的相关文档
