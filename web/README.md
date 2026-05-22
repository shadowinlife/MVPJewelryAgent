# 曜齐 YAOQI · 玉石珠宝鉴定估价助手 (Web)

> 私有版 Web MVP — 当前里程碑 **M1 Foundation**(项目骨架 + 品牌主题 + 自研组件 + Mock Route Handlers)。
> 业务需求源:`docs/Product-Spec_v0.4.md` / UI 需求源:`docs/UI-Spec_v0.3.1.md` / 路线图:`docs/roadmap.md`

---

## 0. 这是什么 / 不是什么

- **是**:一个用于品牌方/项目方/早期用户演示完整产品形态的 Mock 流程 MVP(Product-Spec §3 Level 2)。
- **不是**:接入真实 OSS、真实 OCR、真实 AI 报告生成的生产系统。所有数据均为本地 JSON Mock。

---

## 1. 技术栈

| 层 | 选型 | 备注 |
|----|------|------|
| 框架 | Next.js **16.2.6** App Router | ⚠️ 与 Next 15 有差异,写代码前请读 `node_modules/next/dist/docs/` |
| 语言 | TypeScript 5 | strict mode |
| 样式 | Tailwind CSS v4 | `@theme` 指令注入品牌色,无 `tailwind.config.ts` |
| UI 组件 | shadcn/ui (`base-nova` style) | 基于 `@base-ui/react`,非 Radix |
| 字体 | next/font (Inter + Cormorant + Noto Sans/Serif SC) | 自托管,无外部请求 |
| 图标 | lucide-react | 全站禁用 emoji 当图标 |
| Mock 后端 | Next.js Route Handlers | 返回 `lib/mock/*.json` |
| Cookie 会话 | next/headers `cookies()` | M1 仅 httpOnly 标识位,无真实加密 |

---

## 2. 本地启动

```bash
cd web
npm install
cp .env.example .env.local
npm run dev
# 访问 http://localhost:3000  → 默认重定向到 /dev/components 组件预览页
```

### Mock 登录账号

- **用户端**:任意 11 位手机号(13 开头)+ 任意 6 位数字验证码即可登录,会绑定到 `lib/mock/users.json` 中的第一位演示用户。
- **管理端**:`admin` / `yaoqi2026`(写在 `lib/mock/users.json` 的 `admin` 字段)。

> ⚠️ 这是 Mock 凭证,**绝对不要**写到任何生产配置或真实部署中。M3 阶段会被真后端 JWT 替代。

---

## 3. 目录结构(M1 完成状态)

```
web/
├── app/
│   ├── (dev)/dev/components/         # M1 组件预览页(M2 起可删除)
│   ├── api/
│   │   ├── auth/{login,admin-login,logout,me}/route.ts
│   │   ├── cases/route.ts + [id]/route.ts
│   │   ├── ocr/[caseId]/route.ts
│   │   ├── reports/[caseId]/route.ts
│   │   ├── memberships/route.ts
│   │   └── admin/{status,users}/route.ts
│   ├── globals.css                   # 品牌 token + shadcn 语义 token 映射
│   ├── layout.tsx                    # 字体注入 + 全局 html/body
│   └── page.tsx                      # M1: redirect → /dev/components
├── components/
│   ├── ui/                           # shadcn 生成
│   └── yaoqi/                        # 8 个自研业务组件 + index.ts
├── lib/
│   ├── api-client.ts                 # 统一 fetch 封装
│   ├── auth.ts                       # cookies 会话 (Mock)
│   ├── utils.ts                      # cn() helper
│   ├── mock/*.json                   # 全部 Mock 数据
│   └── types/domain.ts               # 共享类型
└── public/mock/images/*.svg          # 占位图(手镯/吊坠/钻戒/3 张证书)
```

---

## 4. 已实现的 Mock API

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

所有响应统一形如:
```json
{ "ok": true, "data": <T>, "source": "mock" }
```

---

## 5. 品牌主题(UI-Spec §2.3)

颜色定义在 `app/globals.css` 的 `@theme` 块,可以直接以 utility 形式使用:

| Token | Hex | Tailwind 用法 |
|-------|-----|--------------|
| ivory (主背景) | `#F8F4EA` | `bg-ivory` |
| cream (卡片背景) | `#F3EBDD` | `bg-cream` |
| ink (主文字) | `#1F1B16` | `text-ink` |
| gold-antique (主 CTA) | `#B08A45` | `text-gold-antique` |
| jade (强调 / 成功) | `#5E7D62` | `bg-jade` |
| danger | `#A64036` | `text-danger` |

shadcn 语义 token (`bg-primary`, `bg-background`, ...)已映射到对应品牌色,所以 `<Button>` 默认就是古金色。

---

## 6. 红线(务必遵守)

- ❌ 不在前端任何位置嵌入真实 API Key / 后端账号密码
- ❌ 不展示完整 OSS 永久 URL,只用签名 URL(M3 才接真 OSS)
- ❌ 不用前端 hidden 隐藏高级会员内容 — 后端必须裁剪
- ❌ 不生成公开可分享的客户简洁版链接(UI-Spec §11.1)
- ❌ 不使用 emoji 当 UI 图标,统一 lucide-react
- ❌ 不写 "绝对保真 / 100% 准确 / 一定升值"(UI-Spec §16.1)

---

## 7. 下一步(路线图)

- **M2 — User Pages**:实现 10 个用户端页面(`/login`、`/dashboard`、`/cases/new` 5 步向导、`/cases/[id]`、客户简洁版等)
- **M3 — Admin Pages**:实现 11 个管理后台页面,重点 `/admin/dashboard` 接入状态看板
- **M4 — Real Backend**:接入真 OSS / OCR / AI / 鉴权,替换 Mock Route Handlers

详见 [`docs/roadmap.md`](../docs/roadmap.md)。
