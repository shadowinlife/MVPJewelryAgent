# 曜齐珠宝鉴定估价助手私有版 Technical Spec

版本：v0.1 技术草案  
更新时间：2026-05-19  
对应产品文档：Product-Spec_v0.4.md  
对应 UI 文档：UI-Spec_v0.3.1.md  
文档用途：交付给工程师与 AI 编程代理，用于明确 Web MVP 的技术架构、数据结构、API、OSS、AI/OCR、权限、安全、部署和验收边界。  
产品名称：曜齐珠宝鉴定估价助手私有版  
英文工作名：YAOQI Jewelry Appraisal Assistant Private MVP

---

## 0. 技术总原则

本项目第一阶段只做轻量 Web MVP，不做原生 App，不做微信小程序，不做支付，不做复杂会员订阅，不做微服务。

但 MVP 不能做成纯静态页面或只有 Mock 数据的演示站。它必须逐步具备真实业务闭环能力：

1. 用户可以登录。
2. 用户可以创建案例。
3. 用户可以上传图片和证书。
4. 文件进入项目方云账号下的私有 OSS。
5. 案例进入项目方数据库。
6. OCR 和 AI 调用由后端统一控制。
7. 管理员可以查看、筛选、导出数据。
8. 普通用户不能访问他人数据或原图永久链接。
9. 所有核心数据可备份、可迁移、可导出。

---

## 1. 推荐技术栈

### 1.1 前端

推荐：

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui，若工程师熟悉

原因：

- 适合快速构建 Web MVP。
- 便于后续做响应式手机浏览器页面。
- 生态成熟，AI 编程工具支持较好。
- 可同时承载用户端和管理后台。

### 1.2 后端

推荐二选一：

方案 A：Next.js API Routes / Server Actions 作为轻量单体后端  
适合：极简 MVP，前后端一体化，部署简单。

方案 B：Node.js NestJS / Express 单体后端  
适合：后续 API 规模会变大，需要更清晰分层。

可接受备选：Python FastAPI  
适合：工程师更熟 Python，后续要做更多 AI / 数据处理任务。

### 1.3 数据库

推荐：

- PostgreSQL，优先
- MySQL，可接受

建议优先 PostgreSQL，原因：

- JSON 字段支持强。
- 适合复杂报告、AI 输出、OCR 原文、标签等半结构化数据。
- 后续做检索、统计和扩展更灵活。

### 1.4 ORM

推荐：

- Prisma，若采用 Node.js / Next.js
- SQLAlchemy，若采用 FastAPI

### 1.5 文件存储

推荐：

- 阿里云 OSS 私有 Bucket

原则：

- 不允许 public-read。
- 不允许 public-read-write。
- 前端不得直接持有长期 AccessKey。
- 前端通过后端获取上传凭证或签名。
- 图片访问通过短时效签名 URL。

### 1.6 OCR

推荐：

- 阿里云 OCR，主方案
- 多模态大模型视觉，辅助方案

### 1.7 AI

推荐：

- ChatGPT API，首版
- 模型名、价格和具体调用方式以开发时 OpenAI 官方接口为准

调用原则：

- API Key 只存在服务端环境变量中。
- 不允许前端暴露 API Key。
- 所有调用记录写入日志表。
- 支持模型分层：低成本结构化模型 + 高能力多模态模型。

---

## 2. 系统架构

### 2.1 MVP 架构

```text
用户手机/电脑浏览器
        ↓
响应式 Web 前端
        ↓
单体后端 API
        ↓
PostgreSQL / MySQL 数据库
        ↓
阿里云 OSS 私有文件存储
        ↓
阿里云 OCR / ChatGPT API
        ↓
管理后台
```

### 2.2 不做的架构

MVP 不做：

- 微服务
- Kubernetes
- 复杂 Serverless 编排
- 多云部署
- 独立 BI 系统
- 实时 IM
- 支付系统
- App Store 上架
- 微信小程序首发

---

## 3. 环境划分

### 3.1 必须有的环境

至少保留：

- local：工程师本地开发
- staging：测试环境 / 内测环境
- production：正式公测环境，后续

### 3.2 环境变量

必须提供 `.env.example`，不得把真实密钥提交到 Git。

示例字段：

```text
APP_ENV=local
APP_URL=http://localhost:3000
DATABASE_URL=
JWT_SECRET=
ALIYUN_OSS_REGION=
ALIYUN_OSS_BUCKET=
ALIYUN_OSS_ACCESS_KEY_ID=
ALIYUN_OSS_ACCESS_KEY_SECRET=
ALIYUN_OCR_ACCESS_KEY_ID=
ALIYUN_OCR_ACCESS_KEY_SECRET=
OPENAI_API_KEY=
SMS_PROVIDER=
SMS_ACCESS_KEY_ID=
SMS_ACCESS_KEY_SECRET=
WECHAT_APP_ID=
WECHAT_APP_SECRET=
```

### 3.3 密钥原则

- 所有密钥归项目方账号所有。
- 工程师使用子账号或临时授权。
- 不允许工程师个人账号长期持有核心资源。
- 不允许把真实密钥写在代码里。
- 不允许把真实密钥发到公共仓库。

---

## 4. 角色与权限

### 4.1 用户角色

建议角色：

- guest：未登录用户
- free_user：免费用户
- member_basic：个人基础版
- member_pro：个人高级版
- business：商业版
- business_pro：商业高级版
- admin：管理员
- super_admin：超级管理员

### 4.2 权限原则

- 普通用户只能查看自己的案例。
- 普通用户不能查看他人案例。
- 普通用户不能查看 OSS 原始地址。
- 普通用户不能导出全量数据。
- 高级价格内容必须由后端裁剪，不得只靠前端隐藏。
- 管理员可以查看全量案例，但原图查看和数据导出必须记录日志。
- 超级管理员可以管理管理员账号和关键配置。

---

## 5. 数据库 Schema 草案

### 5.1 users 用户表

字段建议：

- id
- phone
- phone_verified_at
- wechat_openid
- wechat_unionid
- nickname
- avatar_url
- role
- status
- created_at
- updated_at
- last_login_at

### 5.2 memberships 会员表

字段建议：

- id
- user_id
- membership_level
- membership_start_at
- membership_expire_at
- report_quota_total
- report_quota_used
- manual_grant_reason
- granted_by_admin_id
- created_at
- updated_at

### 5.3 cases 案例表

字段建议：

- id
- case_no
- user_id
- title
- category
- purpose
- source_channel
- status
- risk_level
- material_guess
- quality_level
- sell_intent
- recycle_intent
- consignment_intent
- user_expected_price
- asking_price
- purchase_price
- transaction_price
- auction_start_price
- weight
- dimensions
- bead_size
- ring_size
- certificate_institution
- certificate_no
- user_note
- seller_text
- admin_note
- data_source
- is_mock
- created_at
- updated_at

### 5.4 case_files 文件表

字段建议：

- id
- case_id
- user_id
- file_type
- original_filename
- mime_type
- size_bytes
- oss_bucket
- oss_key_original
- oss_key_preview
- oss_key_watermarked
- width
- height
- upload_status
- is_private
- created_at

file_type 可选：

- jewelry_natural_light
- jewelry_lighted
- certificate
- hand_wearing
- back_side
- flaw_detail
- auction_screenshot
- seller_text_screenshot
- video
- report_file
- knowledge_file

### 5.5 ocr_results OCR 结果表

字段建议：

- id
- case_id
- file_id
- provider
- raw_text
- parsed_json
- confidence_level
- user_corrected_json
- status
- error_message
- created_at
- updated_at

### 5.6 ai_reports AI 报告表

字段建议：

- id
- case_id
- user_id
- report_type
- model_name
- prompt_version
- input_summary_json
- output_json
- full_markdown
- user_visible_markdown
- customer_simple_markdown
- price_fields_json
- risk_fields_json
- status
- error_message
- created_at
- updated_at

report_type 可选：

- internal_full
- user_visible
- customer_simple
- admin_reviewed

### 5.7 ai_call_logs AI 调用日志表

字段建议：

- id
- user_id
- case_id
- task_type
- model_name
- input_token_count
- output_token_count
- cost_estimate
- status
- error_message
- created_at

### 5.8 admin_operation_logs 管理员操作日志表

字段建议：

- id
- admin_id
- action
- target_type
- target_id
- detail_json
- ip_address
- user_agent
- created_at

### 5.9 knowledge_files 知识文件表

字段建议：

- id
- title
- file_type
- oss_key
- original_filename
- parsed_status
- parsed_json
- enabled
- uploaded_by_admin_id
- created_at
- updated_at

### 5.10 import_jobs 历史导入任务表

字段建议：

- id
- file_id
- job_type
- status
- total_count
- success_count
- error_count
- error_detail_json
- created_by_admin_id
- created_at
- updated_at

---

## 6. API 清单草案

### 6.1 Auth API

- POST /api/auth/send-sms-code
- POST /api/auth/login-by-sms
- POST /api/auth/wechat-login
- POST /api/auth/logout
- GET /api/auth/me

### 6.2 Case API

- POST /api/cases
- GET /api/cases
- GET /api/cases/:id
- PATCH /api/cases/:id
- POST /api/cases/:id/archive
- POST /api/cases/:id/delete-request

### 6.3 Upload API

- POST /api/uploads/presign
- POST /api/uploads/complete
- GET /api/files/:id/signed-url
- GET /api/files/:id/preview-url

### 6.4 OCR API

- POST /api/cases/:id/ocr/start
- GET /api/cases/:id/ocr/result
- PATCH /api/cases/:id/ocr/correct

### 6.5 AI Report API

- POST /api/cases/:id/reports/generate
- GET /api/cases/:id/reports/latest
- GET /api/cases/:id/reports/customer-simple
- POST /api/cases/:id/reports/regenerate

### 6.6 Admin API

- GET /api/admin/users
- PATCH /api/admin/users/:id
- GET /api/admin/cases
- GET /api/admin/cases/:id
- PATCH /api/admin/cases/:id
- POST /api/admin/cases/:id/review
- GET /api/admin/export/users
- GET /api/admin/export/cases
- GET /api/admin/export/leads
- GET /api/admin/logs/ai
- GET /api/admin/logs/ocr
- GET /api/admin/logs/operations

### 6.7 Knowledge / Import API

- POST /api/admin/knowledge-files
- GET /api/admin/knowledge-files
- PATCH /api/admin/knowledge-files/:id
- POST /api/admin/import-jobs
- GET /api/admin/import-jobs/:id

### 6.8 System Status API

- GET /api/admin/system/status

返回内容应包括：

- database_connected
- oss_connected
- ocr_connected
- openai_connected
- sms_connected
- wechat_connected
- mock_mode_enabled
- app_version

---

## 7. OSS 文件策略

### 7.1 Bucket 策略

MVP 可先使用一个私有 Bucket，通过目录区分：

```text
/user-upload-original/
/user-upload-preview/
/user-upload-watermarked/
/certificate-images/
/report-files/
/knowledge-files/
/system-temp/
```

后续数据规模变大后再拆分 Bucket。

### 7.2 上传流程

推荐流程：

1. 前端请求后端生成上传签名。
2. 后端校验用户权限。
3. 后端返回短时效上传凭证或签名 URL。
4. 前端直接上传到 OSS。
5. 前端通知后端上传完成。
6. 后端写入 case_files。
7. 后端触发预览图、水印图、OCR 或 AI 流程。

### 7.3 访问流程

推荐流程：

1. 前端请求文件预览。
2. 后端校验用户是否有权访问该文件。
3. 后端生成短时效签名 URL。
4. 前端展示水印预览图。
5. 原图仅管理员或系统处理可访问。

### 7.4 安全要求

- Bucket 默认私有。
- 禁止公共读写。
- 图片链接短时效。
- 管理端查看原图需记录日志。
- 普通用户不返回原图 OSS Key。
- 高价值案例可设置更短链接有效期。

---

## 8. AI 流程

### 8.1 报告生成流程

1. 用户提交案例。
2. 系统整理基础字段。
3. OCR 提取证书字段。
4. 用户确认或修正 OCR 字段。
5. 后端构造 AI 输入。
6. AI 生成内部完整报告。
7. 系统根据会员等级裁剪展示内容。
8. 生成客户简洁版报告。
9. 写入 ai_reports 和 ai_call_logs。

### 8.2 报告版本

至少保留：

- internal_full：内部完整报告
- user_visible：用户当前会员可见报告
- customer_simple：客户简洁版报告
- admin_reviewed：人工复核版

### 8.3 权限裁剪原则

- 不允许前端拿到完整报告后自行隐藏。
- 后端根据用户会员等级返回对应版本。
- 高级价格字段、回收价、压价策略、渠道判断、内部相似案例不应返回给低权限用户。

---

## 9. OCR 流程

### 9.1 OCR 处理流程

1. 用户上传证书图。
2. 图片进入 OSS 私有目录。
3. 后端调用 OCR。
4. OCR 返回原始文本。
5. 系统抽取结构化字段。
6. 用户确认或修改。
7. 保存 raw_text、parsed_json、user_corrected_json。
8. AI 使用人工确认后的字段。

### 9.2 OCR 失败处理

失败后允许：

- 重新识别
- 手动录入
- 跳过 OCR
- 管理员后台复核

---

## 10. Mock 与真实接入控制

### 10.1 必须可配置

系统应通过环境变量控制 Mock 模式：

```text
MOCK_AUTH=false
MOCK_OSS=false
MOCK_OCR=false
MOCK_AI=false
MOCK_DATABASE=false
```

### 10.2 Mock 数据标识

所有 Mock 数据必须带字段：

```text
is_mock=true
```

管理后台必须能筛选 Mock 数据和真实数据。

### 10.3 禁止事项

- 禁止把 Mock 报告当真实报告展示给正式用户。
- 禁止把 Mock 数据混入正式导出结果而不标识。
- 禁止只做前端 Mock 后宣称业务闭环完成。

---

## 11. 数据导出

### 11.1 P0 导出能力

必须支持：

- 用户导出
- 案例导出
- 高价值回流线索导出
- AI/OCR 失败记录导出

### 11.2 导出字段

案例导出至少包括：

- case_no
- user_id
- phone_masked
- membership_level
- category
- purpose
- source_channel
- risk_level
- sell_intent
- recycle_intent
- asking_price
- purchase_price
- transaction_price
- material_guess
- quality_level
- report_status
- created_at
- updated_at

### 11.3 导出安全

- 仅管理员可导出。
- 导出前二次确认。
- 导出操作写入 admin_operation_logs。
- 敏感字段可脱敏。

---

## 12. 部署建议

### 12.1 MVP 部署

可选：

- 阿里云 ECS + Nginx + Node.js 服务
- 阿里云轻量应用服务器
- Vercel 前端 + 阿里云后端，若网络和备案策略允许

国内用户优先建议阿里云统一部署，降低 OSS、数据库、短信、OCR 集成复杂度。

### 12.2 域名与 HTTPS

必须：

- 域名归项目方账号所有。
- HTTPS 启用。
- 证书归项目方控制。

### 12.3 备份

MVP 起步就应有：

- 数据库每日备份
- OSS 生命周期策略
- 重要知识文件备份
- 数据库导出脚本

---

## 13. 本地运行要求

工程师必须提供 README，说明：

1. 如何安装依赖。
2. 如何配置 `.env`。
3. 如何初始化数据库。
4. 如何运行本地服务。
5. 如何创建管理员账号。
6. 如何切换 Mock / 真实模式。
7. 如何运行基础测试。

README 面向非工程师也应能看懂。

---

## 14. 测试要求

### 14.1 P0 测试场景

必须测试：

- 用户登录
- 创建案例
- 上传图片
- 上传证书
- OCR 成功
- OCR 失败
- 用户修正 OCR 字段
- AI 生成报告
- AI 失败
- 会员权限裁剪
- 普通用户访问他人案例被拒绝
- 普通用户无法获取原图永久链接
- 管理员查看案例
- 管理员导出数据
- 管理员查看系统接入状态

### 14.2 安全测试

必须测试：

- 未登录访问接口
- 普通用户访问他人案例
- 低权限用户查看高级价格字段
- 前端抓包是否能拿到完整报告
- OSS 链接过期是否失效
- 删除和导出是否有日志

---

## 15. v0.1 技术验收标准

### 15.1 代码交付

- 项目能本地运行。
- README 清楚。
- `.env.example` 完整。
- 数据库 Schema 可初始化。
- 前端页面与 UI-Spec_v0.3.1 对齐。
- 后端 API 与本技术文档对齐。

### 15.2 业务闭环

- 用户可真实登录，或明确为 Mock 登录。
- 用户可真实创建案例。
- 案例可真实写入数据库。
- 图片可真实上传至 OSS，或明确为 Mock。
- OCR 可真实调用，或明确为 Mock。
- AI 可真实调用，或明确为 Mock。
- 管理员可查看真实数据和 Mock 数据区别。

### 15.3 数据资产

- 数据库归项目方账号控制。
- OSS 归项目方账号控制。
- 域名归项目方账号控制。
- API Key 不暴露在前端。
- 数据可导出。
- 图片不公开裸奔。

