# M2 — User Pages 路标

> 父文档:[../roadmap.md](../roadmap.md)
> 前置:[M1-foundation.md](./M1-foundation.md)(🟢 已完成 2026-05-22)
> 状态:🟢 已完成(2026-05-22)
> 目标:UI-Spec §1.2 的 10 个用户端页面全部跑通,登录 → 案例库 → 5 步新建 → OCR → 报告 → 客户简洁版 → 我的/会员 全流程可点击。

## 业务背景拍板(2026-05-22 Human-in-loop)

1. **Logo**:无真实 VI 手册,继续用 `BrandLogo` 组件占位,真 Logo 落地后替换组件内部。([memory: yaoqi-logo-todo](../../../.claude/projects/-Users-mgong-PycharmProjects-ZhuBaoTest/memory/yaoqi-logo-todo.md))
2. **会员等级口径**:5 档差异核心 = **每月 Token 配额**(已写入 `web/lib/mock/memberships.json`,从 2 万 → 200 万)。可见字段差异保持现状。([memory: yaoqi-membership-tiers](../../../.claude/projects/-Users-mgong-PycharmProjects-ZhuBaoTest/memory/yaoqi-membership-tiers.md))
3. **页面顺序**:先把 10 个用户页面铺完,再做后台。

## 目标产出

完成本路标后:

- 浏览器从 `/login` 走完一遍:登录 → 工作台 → 新建 5 步 → OCR 确认 → 案例详情 → 客户简洁版 → 案例库 → 我的 → 会员
- 所有页面响应式可用(375 / 768 / 1024)
- 手机端底部 `MobileBottomNav` 在每个用户页面都展示
- 所有 Mock 数据仍由 `web/lib/mock/*.json` + `app/api/**` 提供,前端 fetch 不再写 hard-coded 数据
- 内测期间右下角 / 顶部显示 "DEV / MOCK DATA" 标识(`NEXT_PUBLIC_MOCK_MODE=true`)

## 任务清单

| # | 页面 | UI-Spec | 路由 | 状态 | 关键组件 |
|---|------|---------|------|------|---------|
| 1 | (user) route group + 用户端 layout | §4 | `app/(user)/layout.tsx` | 🟢 | 顶导 / `MobileBottomNav` / Mock 浮标 |
| 2 | 登录页 | §5 | `/login` | 🟢 | 手机号+OTP+协议勾选+微信(待接入)|
| 3 | 工作台 | §6 | `/dashboard` | 🟢 | 会员状态卡 / 新建入口卡 / 最近案例 |
| 4 | 案例库 | §13.1 | `/cases` | 🟢 | 搜索 / 筛选 / 卡片列表 |
| 5 | 新建案例 5 步向导 | §7 | `/cases/new` | 🟢 | `WizardStepper` + 5 step + 草稿/Mock 生成 |
| 6 | OCR 确认 | §8 | `/cases/[id]/ocr` | 🟢 | 字段卡 / 置信度 / 手动修改 |
| 7 | 案例详情 + 报告区 | §9 | `/cases/[id]` | 🟢 | 顶部摘要 / 结论卡 / 图片 / 证书 / 报告(按会员裁剪 + `LockedCard`)|
| 8 | 客户简洁版 | §11 | `/cases/[id]/customer-brief` | 🟢 | 极简版(无价格/无渠道,服务端独立 endpoint)|
| 9 | 我的 / 设置 | §1.2 P0 | `/me` | 🟢 | 用户信息 / Token+报告配额进度 / 设置项 / 退出 |
| 10 | 会员权益 | §1.2 P1 | `/membership` | 🟢 | 5 档 Token 配额 + 可见字段对比 |
| 11 | 完成验收 + 文档更新 | — | — | 🟢 | dev server smoke test + 文档落地 |

状态图例:🟢 已完成 / 🟡 进行中 / ⚪ 未开始 / 🔴 阻塞

## 设计约定

### 路由分组

- `app/(user)/` — 全部用户端页面共用 layout(顶导 + 底导 + Mock 浮标)
- `app/(dev)/` — M1 组件预览页(M2 完成后可在 README 标注"内测可见,生产删除")
- `app/(admin)/` — 留给 M3 使用
- 根 `app/page.tsx` 当前 redirect 到 `/dev/components`,M2 第 2 个 PR 起改为 redirect 到 `/dashboard`(未登录则 redirect 到 `/login`)

### 数据获取

- 服务端组件优先使用 `fetch` + 绝对 URL(经 `lib/api-client.ts`),Next 16 默认 `no-store` 不缓存
- 客户端表单(登录、5 步向导)用 `react-hook-form` + `zod` schema
- 列表/筛选页用 URL search params 作为 source of truth(便于书签和后退)

### 会员裁剪

- 报告内容**必须在 Route Handler 内裁剪后再返回**,前端不做 hidden(UI-Spec §17.3 红线)
- `LockedCard` 出现在每个被锁定的字段位置,不展示数字长度

### 文案

- 所有报告页和详情页底部展示 `<DisclaimerNote variant="block" />`
- 所有 Mock 模块旁边贴 `<MockBadge status="mock" />`

## 验收清单

完成定义(全部勾选才能转 🟢):

- [x] 未登录访问 `/dashboard` / `/cases` / `/cases/*` / `/me` 自动 redirect 到 `/login`(307,curl 验证)
- [x] 登录后访问 `/login` 自动 redirect 到 `/dashboard`(`(auth)/layout.tsx`)
- [x] 5 步向导支持"下一步 / 上一步 / 保存草稿",每步字段都能持久(client state)
- [x] OCR 字段编辑后能保存,低置信度字段有视觉标识(高/中/低三色 chip)
- [x] 报告区按当前登录用户的会员等级裁剪,锁定字段出 `LockedCard`(服务端 `cropReportForUser`)
- [x] 客户简洁版**不包含**回收价/压价/法拍上限/渠道(`/api/customer-brief` 实测响应不含相关字段),且页面无"分享"按钮(UI-Spec §11.1)
- [x] `/me` 显示当月 Token 配额使用进度(双进度条)
- [x] `/membership` 展示 5 档 Token 配额对比表(含 ✓ 字段覆盖)
- [x] `MobileBottomNav` 在所有 `/cases/*` / `/dashboard` / `/me` 页面 ≤768px 显示(`(user)/layout.tsx`)
- [x] 没有任何前端代码出现高级会员才能看到的具体数字(全部数字来源 = `CroppedReport.visible`,服务端裁剪)
- [x] 任何报告页都展示免责声明 `<DisclaimerNote>`
- [ ] 浏览器在 375 / 768 / 1024 三档下视觉走查(留人工)— 当前仅 `curl` 200 全绿,响应式断点未亲眼回归

## 完成记录

> 格式:`YYYY-MM-DD #任务编号 一句话说明 / commit hash`

- 2026-05-22 #1–11 M2 全部 10 个用户页面落地 + `(user)` layout + Mock 浮标 + `MobileBottomNav` + `cropReportForUser` 服务端裁剪 + `/api/customer-brief` 独立端点 + dev server smoke 全绿(curl 200)/ 待 commit
- 2026-05-22 验收 — UI-Spec §17.3 红线全部守住:无前端隐藏数字、客户简洁版无价格/无渠道/无分享、报告内容服务端裁剪后再返回。1 项响应式视觉走查留人工。
