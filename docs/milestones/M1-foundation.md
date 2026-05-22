# M1 — Foundation 路标

> 父文档:[../roadmap.md](../roadmap.md)
> 状态:🟢 已完成(2026-05-22)
> 目标:项目能 `npm run dev` 起来,品牌设计系统、共享组件、mock 数据契约就绪。

> ⚠️ 与计划差异:实际安装的是 Next.js **16.2.6**(create-next-app 默认),不是计划中的 15。
> Next 16 要求 Route Handler 的 `ctx.params` 必须 `await`,使用全局 `RouteContext<'...'>` 帮助器类型。
> Tailwind v4 用 `@theme` 指令注入品牌色,无 `tailwind.config.ts`。

## 目标产出

完成本路标后,任何后续页面开发都能直接基于以下基础工作:

- Next.js 15 App Router 工程骨架可运行
- 品牌色 / 字体 / 共享业务组件可直接 import
- 三个演示案例的 mock 数据可通过 `/api/cases` 等接口访问
- 后续工程师/AI 代理通过 README 能 30 分钟内本地起服

## 任务清单

| # | 任务 | 状态 | 产出文件 |
|---|------|------|---------|
| 1 | 写 roadmap.md | 🟢 | `docs/roadmap.md` |
| 2 | 写本路标文件 | 🟢 | `docs/milestones/M1-foundation.md` |
| 3 | 写 3 个核心 skills 文件 | 🟢 | `skills/product-manager.md`, `skills/ui-ux-designer.md`, `skills/frontend-engineer.md` |
| 4 | Next.js 16 + TS + Tailwind v4 初始化 | 🟢 | `web/package.json`, `web/tsconfig.json`, `web/next.config.ts` |
| 5 | shadcn/ui 安装与基础组件生成 | 🟢 | `web/components.json`, `web/components/ui/button.tsx`, `web/lib/utils.ts` |
| 6 | Tailwind 品牌 theme tokens(v4 `@theme`) | 🟢 | `web/app/globals.css` |
| 7 | Google Fonts 注入(next/font) | 🟢 | `web/app/layout.tsx`, `web/app/globals.css` |
| 8 | 8 个 yaoqi 业务组件 | 🟢 | `web/components/yaoqi/*` |
| 9 | Mock 数据 JSON | 🟢 | `web/lib/mock/*.json` |
| 10 | `api-client.ts` + `auth.ts` + `types/domain.ts` | 🟢 | `web/lib/*` |
| 11 | `app/api/` Route Handlers | 🟢 | `web/app/api/**` |
| 12 | 组件预览页 `/dev/components` | 🟢 | `web/app/(dev)/dev/components/page.tsx` |
| 13 | `web/README.md` + `.env.example` | 🟢 | 同名文件 |

状态图例:🟢 已完成 / 🟡 进行中 / ⚪ 未开始 / 🔴 阻塞

## 自研业务组件清单(任务 #8 展开)

放在 `web/components/yaoqi/`:

| 组件 | UI-Spec 出处 | 作用 |
|------|--------------|------|
| `BrandLogo` | §2.1 | 文字 Logo "曜齐 YAOQI" + 古金色边饰 |
| `MockBadge` | §3.2 | 三态(真实可用 / Mock 演示 / 待接入)chip |
| `LockedCard` | §10.2 | 会员锁定卡(古金色描边 + "联系管理员开通") |
| `WatermarkImage` | §12 | SVG 斜向平铺水印的图片容器 |
| `DisclaimerNote` | §16 | 免责声明组件 |
| `StatusBar` | §15 | 案例/OCR/AI/图片 四种状态指示 |
| `MobileBottomNav` | §4.1 | 手机端底部 4 项导航(首页/新建/案例/我的) |
| `WizardStepper` | §7 | 新建案例 5 步进度条 |

## Mock 数据约定(任务 #9 展开)

放在 `web/lib/mock/`:

| 文件 | 内容 |
|------|------|
| `users.json` | 5 个用户,覆盖 free / basic / pro / business / business_pro 5 档会员 |
| `cases.json` | 3 个演示案例:翡翠手镯、和田玉吊坠、钻戒 GIA 1.2ct |
| `reports.json` | 对应 3 个案例的内部完整报告 + 用户可见报告 + 客户简洁版 |
| `ocr-results.json` | 3 个案例的证书 OCR 结果 |
| `memberships.json` | 5 档会员等级解锁字段映射表 |
| `admin-status.json` | 后台接入状态看板数据(登录/OSS/OCR/AI/数据库... 状态) |

## API Route 实际清单(任务 #11 已完成)

放在 `web/app/api/`,全部返回形如 `{ ok, data, source: "mock" }` 的 JSON:

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/auth/login` | POST | 手机号 + OTP 演示登录 |
| `/api/auth/admin-login` | POST | 管理员账号登录 |
| `/api/auth/logout` | POST | 清除会话 |
| `/api/auth/me` | GET | 当前用户 / 管理员状态 |
| `/api/cases` | GET / POST | 案例列表(支持 `?purpose= &risk= &status= &q=`)+ 创建草稿 |
| `/api/cases/[id]` | GET | 案例详情 |
| `/api/ocr/[caseId]` | GET | OCR 字段 |
| `/api/reports/[caseId]` | GET | 分等级报告内容 |
| `/api/memberships` | GET | 会员等级与可见字段 |
| `/api/admin/status` | GET | 管理工作台模块接入状态 |
| `/api/admin/users` | GET | 管理员视图的用户列表(需管理员会话) |

## 验收清单

- [x] `cd web && npm install` 无错误
- [x] `npm run dev` 起服于 `http://localhost:3000`(Turbopack,Ready in 300ms)
- [x] `curl http://localhost:3000/api/cases` 返回 3 个 mock 案例,200
- [x] `curl http://localhost:3000/api/admin/status` 返回功能接入状态,200
- [x] `curl http://localhost:3000/api/{memberships,ocr/case_2026_0001,reports/case_2026_0001,auth/me,cases/case_2026_0001}` 全部 200
- [x] `/dev/components` 页面 200,展示 8 个 yaoqi 组件 + shadcn Button 主题验证
- [x] `web/README.md` 含本地起服 / Mock 模式说明 / Mock 凭证
- [x] `.env.example` 含 `NEXT_PUBLIC_MOCK_MODE=true`
- [ ] 浏览器在 375px / 768px / 1024px 三档下人工检查(留给 review)
- [ ] Chrome DevTools 取色器人工验证 `#B08A45` 古金色实际渲染(留给 review)

## 完成记录

> 任务完成后在此追加,格式:`YYYY-MM-DD #任务编号 一句话说明 / commit hash`

- 2026-05-22 #1-13 全部完成,本地 `npm run dev` 通过 11 条 API 200 校验,`/dev/components` 渲染成功 / commit pending
