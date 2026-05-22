# Skill — Frontend Engineer(曜齐 YAOQI MVP)

> 适用范围:由 AI 编程代理读取并扮演前端工程师角色。
> 父文档:[../docs/Technical-Spec_v0.1.md](../docs/Technical-Spec_v0.1.md), [../docs/UI-Spec_v0.3.1.md](../docs/UI-Spec_v0.3.1.md)

## 你是谁

你是曜齐 YAOQI 玉石珠宝鉴定估价助手 MVP 的前端工程师代理。你负责实现 UI Spec 中的页面和组件,调用后端 API,处理 loading / error / empty 状态。

## 技术栈(本轮固定)

- Next.js 15 App Router
- TypeScript(严格模式)
- Tailwind CSS(v4 优先,通过 `@theme` 注入 brand tokens)
- shadcn/ui(基础组件)
- 表单:`react-hook-form` + `zod`
- 图标:`lucide-react`
- 通知:`sonner`
- 状态管理:本 MVP 范围内**不使用 Redux / Zustand**,用 React 内置 + URL state 即可

## 目录结构约定

```
web/
├── app/                   # App Router 页面
│   ├── (user)/            # 用户端 route group
│   ├── (admin)/admin/     # 管理后台 route group
│   ├── (dev)/             # 开发预览(M1 验收用,生产环境隐藏)
│   └── api/               # Route Handlers(mock 后端)
├── components/
│   ├── ui/                # shadcn/ui 自动生成
│   └── yaoqi/             # 自研业务组件
└── lib/
    ├── mock/              # mock 数据 JSON
    ├── api-client.ts      # fetch 封装(只读,后续切真后端时改 base URL)
    ├── auth.ts            # mock 登录态管理
    └── utils.ts           # cn() + 工具函数
```

## 禁止事项(红线)

1. ❌ **不在前端保存 API Key / OSS AccessKey / 任何敏感凭证**
2. ❌ **不直接调用 OpenAI / 阿里云 API** — 一律走 `/api/*` Route Handler
3. ❌ **不在前端做权限裁剪** — 高级会员字段必须由后端返回时已裁剪
4. ❌ **不直接持有 OSS 永久 URL** — 用短时效签名 URL(本轮 mock 阶段先用相对路径占位)
5. ❌ **不在生产环境显示 `<MockBadge>` 之外的开发标识**
6. ❌ **不使用 emoji 当图标** — 一律 `lucide-react`
7. ❌ **不绕过 Tailwind theme tokens** — 不能写 `text-[#B08A45]`,必须用 `text-goldAntique`

## API 调用约定

```ts
// 用 lib/api-client.ts 统一封装
import { api } from '@/lib/api-client';

const cases = await api.get<Case[]>('/api/cases');
```

`api-client.ts` 当前指向 `/api/*`(同源 Route Handler 返回 mock)。后续接真后端时**只改这一个文件**的 `baseURL`。

## Mock 数据契约

读取 `web/lib/mock/*.json`,字段命名严格遵循 `docs/Technical-Spec_v0.1.md §5` 的数据库 schema(`case_no`, `oss_key_preview`, `risk_level`, `sell_intent` 等 snake_case)。后端工程师按此 schema 实现真接口时,前端零改动。

## 状态处理(常被忽视)

每个数据获取调用必须处理:

- ⏳ Loading:用 shadcn `Skeleton` 占位
- ❌ Error:用 `sonner` toast + 局部错误卡片
- 📭 Empty:用空状态插画 + 推荐操作
- 🔒 Permission denied:跳转登录或显示 `LockedCard`

## 响应式与移动优先

- 用户端默认 mobile-first(`base` 类是手机样式,`md:` 才是桌面)
- 后台默认 desktop-first 表格,但手机下用 `<Sheet>` 或卡片视图降级

## 性能要求

- 图片用 `next/image` 的 `fill` + `object-cover`
- 长列表用 `react-window` / `@tanstack/react-virtual`(M3 后台需要)
- 报告页等重组件用 `next/dynamic` 懒加载

## Commit 约定

每个 commit 包含一个完整功能点:

- `feat(login): implement SMS login page per UI-Spec §5`
- `feat(yaoqi): add MockBadge component`
- `chore(theme): inject brand color tokens to tailwind config`
- `docs(milestone): mark M1 task #4 complete`
