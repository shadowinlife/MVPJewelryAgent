# 曜齐珠宝鉴定估价助手私有版 Product Spec

版本：v0.4 MVP 执行稿  
更新时间：2026-05-19  
文档用途：交付给工程师、Claude Code / Codex / Cursor 等 AI 编程代理，用于明确 Web MVP 的产品边界、数据资产策略、后端与云服务边界、AI/OCR 调用、历史案例导入、后台管理、交付验收、skills 工作流和后续迭代方式。  
产品名称：曜齐珠宝鉴定估价助手私有版  
英文工作名：YAOQI Jewelry Appraisal Assistant Private MVP

---

## 0. v0.4 关键结论

v0.4 在 v0.3 的基础上新增“AI 编程代理可执行交付”视角。核心变化不是扩大 MVP 范围，而是把“工程师一小时做出的可视化 MVP”和“真正可公测的业务 MVP”区分清楚，避免把漂亮页面误认为完整产品。

1. 首发仍坚持：先做响应式 Web MVP + 轻量 Web 管理后台，不急于做原生 App 和微信小程序。
2. v0.4 明确区分四种 MVP：UI 原型 MVP、Mock 流程 MVP、业务闭环 MVP、可公测生产 MVP。
3. 工程师当前展示的一小时成果大概率属于 UI 原型 MVP 或 Mock 流程 MVP，不能直接等同于业务闭环 MVP。
4. 后续开发采用“文档驱动 + skills 驱动 + AI 编程代理 + 人类验收”的方式。
5. skills 不是神秘功能，本质是给 AI 编程代理读取的角色规则、任务流程、代码规范、测试规范和部署规范。
6. 本地 Codex / Claude Code / Cursor 不是必须立刻由用户亲自操作，但项目交付物必须支持用户或未来工程师在本地继续迭代。
7. 工程交付必须包含源码、README、环境变量模板、数据库 Schema、API 清单、部署说明、skills 文件夹、已完成/未完成清单。
8. 第一阶段允许先用 mock 数据跑通前端和交互，但必须在文档和界面中标记哪些功能是真实接入，哪些只是占位。
9. 真正进入公测前，必须接入真实登录、数据库、OSS 私有上传、AI API、OCR、后台、权限控制和数据导出。
10. 云资源必须归曜齐项目方控制，工程师只能使用子账号或临时权限。
11. 用户上传的图片、证书、报告、回收意向、会员行为和案例数据是核心商业资产，必须可导出、可备份、可迁移。
12. v0.4 不把所有细节都塞进 Product Spec，而是要求拆分出 Technical Spec、Database Schema、API Spec、Acceptance Test、README 和 AI Skills。
13. v0.4 的目标是让工程师和 AI 编程代理可以继续迭代，而不是只交付一个看起来好看的页面。

---

## 1. 产品定位

曜齐珠宝鉴定估价助手私有版不是普通“珠宝鉴定小工具”，而是一个面向珠宝创业者、内部团队、注册会员和潜在回收客户的 AI 辅助鉴定估价与用户资产沉淀系统。

产品核心目标：

1. 让用户通过 Web 端上传珠宝图片、证书、价格、尺寸、重量、卖家文案、法拍公告等信息。
2. 系统通过 OCR、AI 多模态分析和历史案例知识库，生成初步鉴定估价报告。
3. 后台沉淀用户、案例、价格区间、出售/回收意向、会员等级和高价值线索。
4. 为曜齐后续二手珠宝回流、寄售、线下成交、直播转卖和私域运营提供数据基础。

一句话定位：

> 曜齐珠宝鉴定估价助手是一款面向珠宝持有者和珠宝创业团队的私有 Web MVP。用户上传珠宝图片、证书和描述后，系统生成初步鉴定意见、价格区间和风险提示，并沉淀为曜齐自有案例库，服务后续二手珠宝回流、直播选品和线下交易闭环。

---

## 2. v0.4 对“AI 造 App”的基本判断

### 2.1 可以接受的判断

“未来属于有想法和跨学科的人”这个方向是成立的。原因是：

- AI 编程代理可以大幅降低从文档到代码的成本。
- 用户拥有珠宝鉴定、资产评估、内容运营、品牌定位和交易场景经验，这是普通工程师没有的业务壁垒。
- 项目是否成立，关键不是谁会写更多代码，而是谁能定义正确问题、控制数据资产、判断输出质量并持续验收。

### 2.2 必须纠正的误解

不能把“1000 字文档生成 App”理解成“一句话自动变成商业系统”。稳定路径是：

```text
商业想法
→ Product Spec
→ UI Spec
→ Technical Spec
→ Database Schema
→ API Spec
→ AI Skills
→ 代码生成
→ 本地运行
→ 测试修 bug
→ 云端部署
→ 公测验收
→ 持续迭代
```

AI 可以提高执行效率，但不能替代：

- 产品边界判断
- 数据资产归属设计
- 真实业务验收
- 隐私与权限控制
- 高价珠宝风险判断
- 商业闭环设计

### 2.3 v0.4 的核心原则

本项目不追求“看起来已经上线”，而追求“可持续迭代、数据归属清楚、可验收、可迁移、可扩展”。

---

## 3. MVP 类型定义

为避免误解，v0.4 明确区分四类 MVP。

### 3.1 Level 1：UI 原型 MVP

特征：

- 页面能打开。
- 布局接近 UI Spec。
- 按钮、卡片、导航基本存在。
- 数据多为静态或假数据。
- 不一定有数据库、登录、OSS、OCR、AI。

用途：

- 验证审美和页面方向。
- 给用户和工程师看产品大概长什么样。

不能用于：

- 公测。
- 存储真实用户数据。
- 证明业务闭环已跑通。

### 3.2 Level 2：Mock 流程 MVP

特征：

- 用户可以点击完整流程。
- 上传、生成报告、案例库可能使用 mock 数据。
- 后端接口可能存在，但部分是假接口或占位接口。
- 可以模拟“提交案例 → 生成报告 → 查看案例”。

用途：

- 验证交互流程。
- 让 AI 编程代理继续补真实接口。

不能用于：

- 对外收集真实敏感数据。
- 宣称已完成正式 AI 鉴定系统。

### 3.3 Level 3：业务闭环 MVP

特征：

- 用户可真实登录。
- 用户可真实上传图片和证书。
- 图片进入项目方 OSS 私有 Bucket。
- 案例写入项目方数据库。
- OCR 可真实识别证书。
- AI API 可真实生成报告。
- 用户可查看自己的历史案例。
- 管理后台可查看用户、案例、报告和失败日志。
- 会员权限字段真实生效。

用途：

- 小范围内测。
- 邀请可信用户提交真实案例。
- 验证报告质量和后台处理效率。

### 3.4 Level 4：可公测生产 MVP

特征：

在 Level 3 基础上增加：

- 域名、HTTPS、基础备案/合规准备。
- 用户协议、隐私政策、AI 免责声明。
- 错误日志、操作日志、备份策略。
- 数据导出。
- 权限越权测试通过。
- OSS 私有访问和短时效签名 URL 验收通过。
- 高级价格字段不被低权限接口返回。
- 生产环境和测试环境隔离。

用途：

- 小范围公测。
- 私域用户试用。
- 直播/线下合作前的真实业务验证。

---

## 4. 首发端与阶段路线

### 4.1 首发端

首发端仍为：

- 响应式 Web 用户端
- Web 管理后台

### 4.2 后续端

后续端为：

- 微信 H5 / 微信小程序
- iOS / Android App

### 4.3 阶段路线

#### 阶段 0：文档和 AI 工程体系整理

目标：让项目可被工程师和 AI 编程代理稳定接手。

交付：

- Product-Spec_v0.4.md
- UI-Spec_v0.4.md 或沿用 UI-Spec_v0.3 并打补丁
- Technical-Spec_v0.1.md
- Database-Schema_v0.1.md
- API-Spec_v0.1.md
- Acceptance-Test_v0.1.md
- README.md
- AI Skills 文件夹

#### 阶段 1：UI 原型 MVP

目标：页面看起来正确。

交付：

- 登录页
- 工作台
- 新建案例页
- 上传页
- 报告页
- 案例库
- 管理后台基础页面

#### 阶段 2：Mock 流程 MVP

目标：所有核心路径可点击、可演示。

交付：

- mock 用户
- mock 案例
- mock 报告
- mock OCR 结果
- mock 后台数据
- 前端路由完整
- 组件结构清晰

#### 阶段 3：真实业务闭环 MVP

目标：接入真实后端和云服务。

交付：

- 真实登录
- 真实数据库
- 真实 OSS 上传
- 真实 OCR
- 真实 ChatGPT API 调用
- 真实后台管理
- 真实权限控制
- 真实数据导出

#### 阶段 4：内测与公测准备

目标：安全、稳定、可追踪。

交付：

- 生产环境部署
- 备份策略
- 错误日志
- 操作日志
- 用户协议
- 隐私政策
- AI 免责声明
- 基础性能测试
- 边界测试

---

## 5. 本项目的核心用户角色

### 5.1 普通注册用户

使用目的：

- 上传个人珠宝。
- 获取初步判断。
- 查看简洁报告。
- 保存历史案例。

权限：

- 只能查看自己的案例。
- 只能查看免费/当前会员等级允许的报告内容。
- 不能查看内部回收价、压价策略、渠道判断和相似内部案例。

### 5.2 会员用户

使用目的：

- 获取更完整价格区间。
- 查看入手价、流通价、复检建议等高级内容。

权限：

- 根据会员等级查看对应报告模块。
- 受次数配额限制。

### 5.3 商业用户 / 内部选品用户

使用目的：

- 法拍评估。
- 直播选品。
- 批量采购辅助判断。

权限：

- 可查看更完整价格策略。
- 可提交更复杂案例。
- 后续可开放批量分析。

### 5.4 管理员

使用目的：

- 管理用户、会员、案例、报告、知识文件。
- 查看 AI/OCR 失败记录。
- 导入历史案例。
- 导出数据。

权限：

- 查看全部案例。
- 修改会员等级。
- 复核报告。
- 导出数据。

### 5.5 超级管理员 / 项目所有者

使用目的：

- 控制系统配置、云资源、管理员权限、敏感数据导出。

权限：

- 管理管理员账号。
- 查看系统日志。
- 管理环境配置。
- 批量导出用户和案例。
- 控制高敏感功能。

---

## 6. MVP P0 功能范围

P0 是进入业务闭环 MVP 必须完成的功能。

### 6.1 用户端 P0

1. 手机号验证码登录。
2. 微信登录预留；若首版工程复杂，可先做微信登录按钮占位，但必须在交付清单标注“未真实接入”。
3. 用户协议、隐私政策、AI 免责声明勾选。
4. 工作台首页。
5. 新建案例。
6. 选择品类。
7. 选择用户目的：购买、出售、回收、法拍、学习、直播选品、客户咨询、商业选品。
8. 上传珠宝图片。
9. 上传证书图片。
10. 填写尺寸、重量、圈口、珠径、叫价、成交价、证书机构、证书编号、卖家文案、备注。
11. 勾选是否有出售/回收意向。
12. OCR 识别证书。
13. 用户确认或修改 OCR 字段。
14. 生成 AI 初步鉴定估价报告。
15. 查看案例详情。
16. 查看历史案例。
17. 查看客户简洁版报告。
18. 复制客户简洁版文本。
19. 图片水印预览。
20. 退出登录。

### 6.2 管理后台 P0

1. 管理员登录。
2. 管理工作台。
3. 用户列表。
4. 会员等级手动修改。
5. 用户禁用/启用。
6. 案例列表。
7. 案例详情。
8. 查看图片、证书、OCR 结果、AI 报告。
9. 修改或补充人工复核意见。
10. 标记案例状态：待处理、已分析、需补图、待复检、已联系、已成交、无效、已归档。
11. 历史 Markdown 案例导入。
12. 知识文件上传。
13. AI/OCR 失败记录。
14. 基础数据导出。

### 6.3 系统 P0

1. 数据库。
2. OSS 私有 Bucket。
3. 短时效签名 URL。
4. 后端鉴权。
5. AI API Key 仅保存在后端环境变量。
6. OCR 服务仅由后端调用。
7. 角色权限控制。
8. 操作日志。
9. 错误日志。
10. 环境变量模板。
11. 本地运行 README。
12. 部署说明。

---

## 7. MVP 暂不做范围

首版不做：

1. 原生 iOS App。
2. 原生 Android App。
3. 微信小程序正式发布。
4. 微信支付。
5. Apple 内购。
6. 复杂订阅系统。
7. 优惠券。
8. 分销返佣。
9. 在线 IM 聊天。
10. 商城。
11. 竞拍系统。
12. 直播间系统。
13. 自动营销推送。
14. 复杂 BI 看板。
15. 多组织、多门店、多员工层级。
16. 大规模爬虫。
17. 本地大模型训练。
18. 自动给出正式鉴定证书。
19. 对外公开分享报告链接。
20. 用户自行公开发布案例社区。

---

## 8. 数据资产与商业闭环

### 8.1 核心数据资产

本系统必须沉淀以下数据：

- 用户手机号。
- 用户微信身份。
- 用户会员等级。
- 用户上传的珠宝图片。
- 用户上传的证书图片。
- OCR 原始文本。
- OCR 修正字段。
- 珠宝品类。
- 尺寸、重量、圈口、珠径等结构化字段。
- 购买价、叫价、起拍价、成交价、心理价。
- AI 报告。
- 内部完整报告。
- 客户简洁版报告。
- 风险等级。
- 流通性判断。
- 是否有出售/回收意向。
- 管理员复核意见。
- 后续联系状态。
- 是否成交或回流。
- 历史案例标签。
- 用户偏好画像。

### 8.2 商业闭环

目标路径：

```text
用户提交案例
→ AI 初步鉴定估价
→ 后台识别高价值线索
→ 管理员/运营人工复核
→ 联系有回收/出售/寄售意向的用户
→ 线下复检或寄售
→ 直播/线下/私域再销售
→ 成交数据反哺案例库
```

### 8.3 数据私有化原则

1. 阿里云账号归项目方所有。
2. OSS Bucket 归项目方所有。
3. 数据库归项目方所有。
4. 域名归项目方所有。
5. OpenAI / AI API 账号归项目方所有。
6. 工程师使用子账号权限，不代持核心资源。
7. 所有数据支持导出。
8. 所有图片和报告支持备份。
9. 不把核心数据锁死在低代码平台或不可导出 SaaS。

---

## 9. 推荐技术架构

### 9.1 推荐路线

MVP 推荐：

- 前端：Next.js + TypeScript。
- UI：Tailwind CSS 或工程师已选定的组件体系。
- 后端：Next.js API Routes / Node.js 后端 / Python FastAPI 三选一，由工程师根据现有项目决定。
- 数据库：PostgreSQL 优先；MySQL 可接受。
- ORM：Prisma 或同等级成熟 ORM。
- 文件存储：阿里云 OSS 私有 Bucket。
- OCR：阿里云 OCR。
- AI：OpenAI / ChatGPT API。
- 短信：阿里云短信或其他合规短信服务商。
- 部署：阿里云 ECS / 轻量服务器 / 容器服务，MVP 不做复杂微服务。
- 管理后台：同一 Web 项目中的 admin 路由，或独立 admin app。

### 9.2 不建议路线

首版不建议：

- 纯前端无后端。
- 纯低代码平台承载核心数据。
- 过度 Serverless 拼接。
- 微服务架构。
- 多云混合。
- App、小程序、Web 三端同时开工。

### 9.3 可接受折中

可以先采用：

- 前端真实 + 后端 mock。
- 后端接口已写好但云服务暂未配置。
- 数据库本地开发环境先跑 SQLite / PostgreSQL Docker，生产再切阿里云数据库。
- OSS 上传先使用本地模拟，生产接阿里云 OSS。

但必须在 README 和交付清单中标注：

- 哪些是真实功能。
- 哪些是 mock。
- 哪些是占位。
- 哪些需要用户提供云账号/API Key 后才能启用。

---

## 10. AI Skills 工作流

### 10.1 skills 的定义

本项目中的 skills 指给 AI 编程代理读取和执行的规则文件，不等同于普通产品文档。

它们通常是 Markdown 文件、规则文件、脚本、提示词模板或目录规范，用于告诉 AI：

- 你现在扮演什么角色。
- 你要遵守什么代码规范。
- 你每次修改前后要检查什么。
- 哪些文件不能改。
- 哪些安全边界不能破坏。
- 任务完成后如何验收。

### 10.2 推荐 skills 目录

建议项目根目录增加：

```text
/skills
  /product-manager.md
  /ui-ux-designer.md
  /frontend-engineer.md
  /backend-engineer.md
  /database-architect.md
  /ai-integration-engineer.md
  /security-engineer.md
  /qa-tester.md
  /devops-engineer.md
  /documentation-writer.md
```

### 10.3 每个 skill 的职责

#### product-manager.md

负责：

- 解释 Product Spec。
- 判断需求是否属于 MVP。
- 防止范围膨胀。
- 输出用户故事和验收标准。

#### ui-ux-designer.md

负责：

- 遵守 UI Spec。
- 保持曜齐品牌视觉。
- 检查手机端可用性。
- 检查会员锁定内容是否泄漏。

#### frontend-engineer.md

负责：

- 实现页面和组件。
- 调用后端 API。
- 处理 loading、error、empty 状态。
- 禁止在前端保存敏感 API Key。

#### backend-engineer.md

负责：

- 实现 API。
- 处理鉴权。
- 调用 OSS、OCR、AI。
- 写入数据库。
- 返回权限裁剪后的数据。

#### database-architect.md

负责：

- 维护 Schema。
- 设计迁移。
- 确保数据可导出。
- 确保核心字段不缺失。

#### ai-integration-engineer.md

负责：

- AI prompt 设计。
- 模型分层调用。
- 成本控制。
- 失败重试。
- 报告结构化输出。

#### security-engineer.md

负责：

- 检查越权访问。
- 检查 OSS 是否公开。
- 检查高级字段是否在低权限接口返回。
- 检查日志和敏感信息泄漏。

#### qa-tester.md

负责：

- 按 Acceptance Test 测试。
- 记录 bug。
- 复测修复。
- 区分 UI bug、功能 bug、安全 bug。

#### devops-engineer.md

负责：

- 本地运行。
- 环境变量。
- 部署。
- 日志。
- 备份。

#### documentation-writer.md

负责：

- 更新 README。
- 更新接口说明。
- 更新已完成/未完成清单。
- 维护交付说明。

### 10.4 用户是否需要本地安装 Codex skills

建议分两步：

第一步：由工程师先交付可运行项目和 skills 文件夹，用户不急着自己安装。

第二步：当项目进入持续迭代期，用户可以在本地安装 Codex / Claude Code / Cursor，并让 AI 读取：

- docs/
- skills/
- README.md
- package.json
- .env.example

用户需要掌握的不是写代码，而是：

- 启动项目。
- 描述需求。
- 运行测试。
- 截图反馈。
- 判断功能是否符合业务。

---

## 11. 交付物清单

工程师交付不能只给一个网址或截图，必须包含以下内容。

### 11.1 代码与项目文件

- 完整源码仓库。
- package.json / requirements.txt 等依赖文件。
- README.md。
- .env.example。
- 数据库迁移文件。
- API 路由文件。
- 前端页面文件。
- 后台页面文件。
- skills 文件夹。
- docs 文件夹。

### 11.2 文档

必须交付：

- Product-Spec_v0.4.md。
- UI-Spec_v0.3.md 或 UI-Spec_v0.4.md。
- Technical-Spec_v0.1.md。
- Database-Schema_v0.1.md。
- API-Spec_v0.1.md。
- Acceptance-Test_v0.1.md。
- Deployment-Guide_v0.1.md。
- Handover-Checklist_v0.1.md。

### 11.3 状态说明

必须交付：

```text
已完成：
- ...

Mock / 占位：
- ...

未接入：
- ...

需要用户提供：
- 阿里云账号
- OSS Bucket
- 数据库连接
- 短信服务配置
- OCR 服务配置
- OpenAI API Key
- 域名
```

### 11.4 本地运行说明

README 必须包含：

1. 如何安装依赖。
2. 如何配置环境变量。
3. 如何启动开发环境。
4. 如何创建数据库。
5. 如何运行迁移。
6. 如何创建管理员账号。
7. 如何进入用户端。
8. 如何进入管理后台。
9. 如何运行测试。
10. 常见报错如何处理。

---

## 12. 数据模型概要

详细字段应单独写入 Database-Schema_v0.1.md。Product Spec 中保留概要。

### 12.1 users 用户表

核心字段：

- id
- phone
- wechat_openid
- wechat_unionid
- nickname
- avatar_url
- role
- status
- membership_level
- membership_start_at
- membership_expire_at
- report_quota_total
- report_quota_used
- created_at
- updated_at
- last_login_at

### 12.2 cases 案例表

核心字段：

- id
- case_no
- user_id
- category
- sub_category
- purpose
- source_channel
- title
- description
- size_text
- weight_text
- ring_size
- bead_size
- certificate_org
- certificate_no
- seller_text
- purchase_price
- asking_price
- auction_start_price
- deal_price
- expected_price
- sell_intent
- recycle_intent
- status
- risk_level
- liquidity_level
- created_at
- updated_at

### 12.3 assets 文件表

核心字段：

- id
- case_id
- user_id
- asset_type
- original_filename
- oss_bucket
- oss_key_original
- oss_key_preview
- oss_key_watermark
- mime_type
- size_bytes
- width
- height
- upload_status
- created_at

### 12.4 ocr_results OCR 表

核心字段：

- id
- case_id
- asset_id
- provider
- raw_text
- structured_json
- confidence_level
- user_corrected_json
- status
- error_message
- created_at

### 12.5 reports 报告表

核心字段：

- id
- case_id
- user_id
- report_type
- internal_report_json
- user_visible_report_json
- customer_brief_text
- material_judgment
- quality_judgment
- price_range_low
- price_range_high
- recycle_price_low
- recycle_price_high
- risk_summary
- recommendation
- model_name
- token_usage
- generation_status
- created_at

### 12.6 admin_reviews 人工复核表

核心字段：

- id
- case_id
- admin_id
- review_status
- manual_material_judgment
- manual_price_opinion
- manual_risk_note
- follow_up_status
- created_at
- updated_at

### 12.7 knowledge_files 知识文件表

核心字段：

- id
- file_type
- title
- oss_key
- parsed_status
- enabled
- created_by
- created_at

### 12.8 import_jobs 导入任务表

核心字段：

- id
- file_id
- import_type
- total_count
- success_count
- failed_count
- error_json
- status
- created_at

### 12.9 audit_logs 操作日志表

核心字段：

- id
- actor_id
- actor_role
- action
- target_type
- target_id
- ip
- user_agent
- detail_json
- created_at

### 12.10 ai_jobs AI 调用日志表

核心字段：

- id
- case_id
- user_id
- task_type
- model_name
- prompt_version
- input_summary
- output_summary
- token_input
- token_output
- cost_estimate
- status
- error_message
- created_at

---

## 13. API 概要

详细接口应单独写入 API-Spec_v0.1.md。

### 13.1 Auth API

- POST /api/auth/send-code
- POST /api/auth/login-phone
- POST /api/auth/login-wechat
- POST /api/auth/logout
- GET /api/auth/me

### 13.2 Case API

- POST /api/cases
- GET /api/cases
- GET /api/cases/:id
- PATCH /api/cases/:id
- POST /api/cases/:id/submit
- POST /api/cases/:id/archive

### 13.3 Asset API

- POST /api/assets/upload-token
- POST /api/assets/confirm-upload
- GET /api/assets/:id/signed-url
- GET /api/assets/:id/preview-url
- DELETE /api/assets/:id

### 13.4 OCR API

- POST /api/cases/:id/ocr
- GET /api/cases/:id/ocr
- PATCH /api/ocr/:id/correction

### 13.5 AI Report API

- POST /api/cases/:id/generate-report
- GET /api/cases/:id/report
- GET /api/cases/:id/customer-brief
- POST /api/cases/:id/regenerate-report

### 13.6 Admin API

- GET /api/admin/users
- PATCH /api/admin/users/:id
- GET /api/admin/cases
- GET /api/admin/cases/:id
- PATCH /api/admin/cases/:id/review
- POST /api/admin/import/markdown
- GET /api/admin/import/jobs
- POST /api/admin/knowledge-files
- GET /api/admin/ai-ocr-failures
- POST /api/admin/export/cases

### 13.7 权限要求

所有 API 必须后端鉴权。不能只靠前端隐藏内容。高级价格字段、回收价、压价策略、内部渠道判断、管理员备注不得返回给低权限用户。

---

## 14. OSS 与图片安全

### 14.1 基础原则

- OSS Bucket 必须私有。
- 不允许 public-read。
- 不允许 public-read-write。
- 前端不得直接暴露永久 OSS 地址。
- 用户访问图片必须通过后端获取短时效签名 URL。
- 普通用户默认只看水印预览图。
- 管理员查看原图必须记录日志。

### 14.2 文件目录建议

```text
/user-upload-original/{user_id}/{case_id}/{file_id}.jpg
/user-upload-preview/{user_id}/{case_id}/{file_id}.jpg
/user-upload-watermark/{user_id}/{case_id}/{file_id}.jpg
/certificate-images/{user_id}/{case_id}/{file_id}.jpg
/report-files/{case_id}/{report_id}.pdf
/knowledge-files/{file_type}/{file_id}.md
/system-temp/{date}/{file_id}
```

### 14.3 水印策略

用户端预览水印：

- 曜齐 YAOQI。
- 案例编号。
- 用户尾号或会员 ID。
- 低透明度。
- 不遮挡关键鉴定区域。

报告截图水印：

- 曜齐珠宝鉴定估价助手。
- AI 辅助判断，仅供参考。
- 案例编号。

---

## 15. AI 与 OCR 策略

### 15.1 AI 分层调用

不要所有任务都使用最高级模型。

任务分层：

1. 文本清洗、OCR 修正、字段抽取：低成本模型。
2. 图片可见特征提取：多模态中低成本模型。
3. 完整鉴定估价报告：中高能力模型。
4. 高价、法拍、证书矛盾、商业采购：高能力模型 + 人工复核。

### 15.2 报告生成流程

```text
用户提交案例
→ 图片和证书入 OSS
→ OCR 识别证书
→ 用户确认/修正 OCR
→ AI 读取结构化字段 + 图片摘要 + 历史知识
→ 生成内部完整报告
→ 按会员权限裁剪用户可见报告
→ 生成客户简洁版
→ 保存报告版本
```

### 15.3 OCR 策略

MVP 主方案：阿里云 OCR。  
辅助方案：大模型视觉做纠错和语义补充。  
不建议首版完全依赖开源 OCR。

### 15.4 AI 输出要求

AI 报告必须结构化输出，至少包含：

- 材质倾向。
- 处理风险。
- 种水/颜色/结构/裂纹/工艺观察。
- 证书信息摘要。
- 图片证据不足提示。
- 价格区间。
- 回收价区间。
- 流通性。
- 是否建议入手。
- 是否建议复检。
- 风险等级。
- 客户简洁版文案。
- 免责声明。

---

## 16. 报告权限与客户简洁版

### 16.1 内部完整报告

仅管理员和高级权限可见。

包含：

- 完整价格带。
- 回收价。
- 压价策略。
- 法拍上限。
- 渠道判断。
- 相似历史案例。
- 管理员备注。
- 高价值回流线索判断。

### 16.2 用户可见报告

根据会员等级展示。

免费用户可见：

- 基础材质倾向。
- 基础风险提示。
- 是否建议复检。
- 粗略等级判断。

高级会员可见：

- 合理入手价。
- 流通成交价。
- 回收参考价。
- 更完整风险分析。

### 16.3 客户简洁版报告

规则：

- 不生成公开分享链接。
- 不生成外部 URL。
- 只允许系统内查看。
- 允许复制文本。
- 用户可自行截图。
- 不包含内部回收价、压价策略、渠道判断和管理员备注。

---

## 17. 历史案例导入

### 17.1 主格式

保留 Markdown 作为原始主文件。

理由：

- 用户已有大量 Markdown 案例。
- Markdown 保留判断过程和经验规则。
- 适合人类维护。
- 适合 AI 解析。

### 17.2 入库流程

```text
管理员上传 Markdown
→ 保存原始文件
→ AI/脚本解析为 JSON
→ 后台显示预览
→ 管理员确认
→ 写入 cases/reports/knowledge 表
→ 异常片段进入错误清单
```

### 17.3 CSV 定位

CSV 不作为主导入格式，只作为后续导出、数据分析和批量校验格式。

---

## 18. UI 范围补充

UI 细节以 UI-Spec_v0.3 为准。v0.4 对 UI 增加以下要求。

### 18.1 页面必须标记 mock 状态

在开发阶段，如果某页面使用 mock 数据，界面右下角或开发环境顶部应显示：

```text
DEV / MOCK DATA
```

生产环境不得显示 mock 数据。

### 18.2 会员锁定不能前端假隐藏

高级内容不能先返回给前端再用 CSS 隐藏。后端必须按权限裁剪字段。

### 18.3 上传状态必须清楚

上传流程必须显示：

- 上传中。
- 上传成功。
- 上传失败。
- 生成预览图中。
- 水印处理中。
- OCR 识别中。
- AI 生成中。

### 18.4 报告页必须显示免责声明

所有报告页必须显示：

> AI 辅助判断仅供参考，不等同于正式鉴定证书，不构成交易、回收或投资承诺。高价珠宝建议送检具备资质的第三方检测机构并结合线下实物复核。

---

## 19. 本地开发与 Codex 使用方式

### 19.1 用户需要掌握的最小操作

用户未来如要自己使用本地 AI 编程代理，最低需要会：

1. 打开项目文件夹。
2. 打开终端。
3. 安装依赖。
4. 启动本地项目。
5. 浏览器访问 localhost。
6. 把报错截图发给 AI。
7. 描述新需求。
8. 按验收清单测试。

### 19.2 推荐本地命令说明

README 应提供类似说明：

```bash
npm install
npm run dev
npm run test
npm run lint
npm run db:migrate
```

### 19.3 AI 编程代理任务模板

后续给 Codex / Claude Code / Cursor 的任务应采用以下模板：

```text
你现在是本项目的【角色】。
请先阅读：
1. docs/Product-Spec_v0.4.md
2. docs/UI-Spec_v0.3.md
3. docs/Technical-Spec_v0.1.md
4. skills/【对应skill】.md

任务：
【清楚描述要改什么】

约束：
1. 不改变已有数据库字段，除非先提出迁移方案。
2. 不把高级价格字段返回给低权限用户。
3. 不在前端保存 API Key。
4. 不把 OSS 设置为公开读。
5. 修改后更新 README 或相关文档。
6. 修改后列出测试步骤。

输出：
1. 修改了哪些文件。
2. 为什么这样改。
3. 如何本地测试。
4. 是否存在未完成项。
```

---

## 20. 验收标准

### 20.1 UI 原型 MVP 验收

- 页面风格符合曜齐品牌调性。
- 登录页、工作台、新建案例、上传页、报告页、案例库、后台页面存在。
- 手机浏览器可正常浏览。
- 主要按钮和路由可点击。
- mock 数据标记清楚。

### 20.2 Mock 流程 MVP 验收

- 用户可从登录页走到新建案例。
- 可模拟上传图片。
- 可模拟 OCR 结果。
- 可模拟生成报告。
- 可查看 mock 案例库。
- 后台可查看 mock 用户和 mock 案例。
- README 标明所有 mock 功能。

### 20.3 业务闭环 MVP 验收

- 用户可真实手机号登录。
- 用户可真实创建案例。
- 用户可真实上传图片和证书。
- 图片进入项目方 OSS 私有 Bucket。
- 案例写入项目方数据库。
- OCR 可真实识别证书。
- 用户可修改 OCR 字段。
- AI 可真实生成报告。
- 用户可查看自己的历史案例。
- 管理员可查看全部案例。
- 管理员可手动设置会员等级。
- 管理员可查看 AI/OCR 失败记录。
- 管理员可导出基础数据。

### 20.4 安全验收

- OSS Bucket 非公开。
- 图片访问必须后端鉴权。
- 图片链接为短时效签名 URL。
- 普通用户不能查看他人案例。
- 普通用户不能获取原图永久地址。
- 高级价格字段不返回给低权限用户。
- API Key 不出现在前端代码。
- 管理员操作有日志。
- 删除和导出有二次确认。

### 20.5 数据资产验收

- 用户表可导出。
- 案例表可导出。
- 报告表可导出。
- 图片 OSS key 可导出。
- 出售/回收意向可筛选。
- 高价值案例可筛选。
- 历史 Markdown 案例可导入。
- 原始文件和结构化数据都保留。

### 20.6 交付验收

工程师交付时必须回答：

1. 当前属于 Level 1、Level 2、Level 3 还是 Level 4？
2. 哪些功能真实可用？
3. 哪些功能是 mock？
4. 哪些功能只是 UI 占位？
5. 哪些功能需要用户提供 API Key 或云服务后才能启用？
6. 如何本地运行？
7. 如何部署？
8. 如何创建管理员？
9. 如何导出数据？
10. 如何继续用 skills 让 AI 迭代？

---

## 21. 风险与取舍

### 21.1 最大风险：误把 UI 当产品

截图能证明页面存在，不能证明产品可用。必须按 Level 1-4 验收。

### 21.2 最大资产：数据

界面可以重做，代码可以重构，但用户数据、珠宝图片、案例判断和回流线索必须从一开始归项目方控制。

### 21.3 最大诱惑：范围膨胀

不要因为 AI 生成代码快，就同时做支付、App、小程序、商城、直播系统。首版只验证上传、分析、沉淀、后台筛选这条主线。

### 21.4 最大技术债：没有文档

AI 生成项目如果没有 README、Schema、API、skills、验收清单，后续会很难维护。

---

## 22. 待确认项

- [待确认] 工程师当前一小时 MVP 属于 Level 1 还是 Level 2。
- [待确认] 当前项目技术栈：Next.js、React、Vue、FastAPI 或其他。
- [待确认] 是否已存在真实后端。
- [待确认] 是否已存在数据库。
- [待确认] 是否已存在 OSS 上传逻辑。
- [待确认] 是否已存在 OCR 接口。
- [待确认] 是否已存在 AI 报告接口。
- [待确认] skills 的具体格式和目录位置。
- [待确认] 是否支持 Codex / Claude Code / Cursor 读取。
- [待确认] 阿里云区域。
- [待确认] 数据库用 PostgreSQL 还是 MySQL。
- [待确认] OpenAI API 使用哪个模型组合。
- [待确认] 阿里云 OCR 具体产品和费用。
- [待确认] 短信验证码供应商。
- [待确认] 用户协议和隐私政策由谁起草。
- [待确认] 是否在隐私政策中加入后续营销触达授权。
- [待确认] 首批内测用户来源和数量。

---

## 23. 发给工程师的确认清单

可以直接复制给工程师：

```text
请基于 Product-Spec_v0.4.md 回答以下问题：

1. 当前你展示的 MVP 属于 Level 1 UI 原型、Level 2 Mock 流程、Level 3 业务闭环，还是 Level 4 可公测生产版本？
2. 当前是否有真实数据库？如果有，请提供 Schema 和迁移文件。
3. 当前是否有真实后端 API？如果有，请提供 API 清单。
4. 当前是否支持真实图片上传？图片保存在哪里？是否使用私有 OSS？
5. 当前是否支持真实登录？手机号和微信是否已接入？
6. 当前是否支持真实 OCR？使用哪个服务？
7. 当前是否支持真实 ChatGPT API？如果没有，需要我提供哪些环境变量？
8. 当前后台管理端完成到什么程度？
9. 当前哪些功能是 mock 数据？
10. 当前哪些功能只是 UI 占位？
11. 你准备交付的 skills 是什么格式？放在哪个目录？
12. 这些 skills 是给 Codex、Claude Code、Cursor，还是通用 AI 编程代理使用？
13. 我是否需要本地安装 Codex 才能继续迭代？如果需要，请提供零代码用户可执行的步骤。
14. 请提供 README、.env.example、部署说明、数据库说明、API 说明和交付清单。
15. 请确认云账号、OSS、数据库、域名、AI API 最终都归项目方控制。
```

---

## 24. v0.4 最终判断

当前最优路线不是“立刻做完整 App”，也不是“只做一个漂亮网页”。

正确路线是：

```text
先用 AI 快速生成 Web MVP 的页面和 mock 流程
→ 用 Product Spec / UI Spec / Technical Spec / skills 固化规则
→ 接入真实后端、数据库、OSS、OCR、AI
→ 做轻量后台和数据导出
→ 小范围内测
→ 根据真实用户案例迭代报告质量
→ 再考虑小程序和 App
```

用户不需要成为程序员，但必须成为：

- 产品方向负责人。
- 数据资产负责人。
- 业务验收负责人。
- AI 工程队指挥者。

这正是本项目 v0.4 的定位。
