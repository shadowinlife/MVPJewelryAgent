# M4 物料收集工作包

> M4 实施前必须收齐的 **12 项物料**逐项执行卡。把 [Deployment Guide §4](../Backend-Deployment-Guide_v0.1.md) 与 [tracker §2.4](./M4-backend-rollout-tracker.md) 的清单展开为业务方可以直接派活、ops/legal/财务可以直接执行的工作包。
>
> 起始:2026-05-23 / 父:[Backend-Deployment-Guide_v0.1.md](../Backend-Deployment-Guide_v0.1.md)、[M4-backend-rollout-tracker.md](./M4-backend-rollout-tracker.md)

---

## 0. 用法

- **谁读这个**:项目方负责人 + ops + 财务 + 法务 + 工程方接口人
- **怎么用**:每周 sync 一次本文 §2 各张卡的"状态"列;阻塞项升级到 tracker §二
- **何时归档**:M4 实施开工后,§2 状态全 ✅ 即可归档(整体移到 `docs/audit/m4-materials-YYYY-MM.md`)

---

## 1. 关键路径与时间线

> **2026-05-26 重要变更**:**M-04 ICP 备案已废弃**。决议:**前端(Next.js)部署在香港节点,后端 + DB + OSS 仍在阿里云华东**;前端在境外节点无需 ICP 备案(工信部要求只对"接入境内服务器的网站")。后端 API 走前端 → 公网 → 阿里云华东 SLB,跨境延迟可接受(MVP);prod 前要测端到端 RTT。原 M-04 关键路径 7-20 天**直接抹掉**,新增 **M-13 HK 前端部署区域确认**(详见 §M-13)。

```text
T-14              T-7         T-1   T
├──────────────────────────────────────────►
│ Azure 订阅+OpenAI ownership+quota(7-14 天)│
                   │ 域名买 + DNS 接管(1-3 天,**无需 ICP**)│
                              │ 短信签名 + 模板审核(1-3 天)│
                              │ 阿里云主账号 / 子账号 / RAM 策略 │
                                          │ KMS CMK + Secret 入库 │
                                          │ OSS Bucket 命名/创建  │
                                                 │ 跳板机 SSH 公钥白名单 │
                                                 │ 监控告警通道接入 │
                              │ HK 前端节点(Vercel / 阿里云 HK / Cloudflare,1-2 天)│
                              │ 真实玉石样本(滚动收集,不卡上线)│
                                                       │ 私调 deployment 名(可选,没有用 gpt-4o-mini 顶)│
```

**硬阻塞**(任一不到则 M4 上不了 production):
- ~~M-04 域名 + ICP 备案~~ **已废弃 2026-05-26** — 前端走 HK 节点,无 ICP 要求
- M-01 阿里云主账号(后端 / DB / OSS 仍在华东)
- M-03 Azure 订阅 + OpenAI ownership
- M-05/M-06 短信签名 + 模板(否则登录验证码下不去)
- **M-13 HK 前端节点选型 + 域名 DNS 接管**(新增;1-3 天)

**软阻塞**(可用 mock / 替代品过渡):
- M-08 私调 deployment(用 `gpt-4o-mini` 顶)
- M-10 真实样本(用 mock 数据跑 staging)
- M-11 告警通道(先邮件,P1 接企微 / 飞书)

**新增技术风险**(因 HK 前端 + 华东后端跨境):
- 端到端 RTT:HK 用户 → HK 前端(< 50ms) → 华东后端(80-150ms,跨境公网)→ AI 调 Azure HK(公网,30-80ms)。MVP 接受;prod 上线前用真用户跑一次 P95 < 800ms 验收。
- CORS:后端必须显式允许 HK 前端域名(Backend-Architecture §11 加 origin 白名单);Stage 4 落地。
- Cookie SameSite:跨域 cookie 需 `SameSite=None; Secure`;影响 Stage 4 JWT cookie 方案。

---

## 2. 12 项执行卡

> 每张卡:`Owner(谁干)/ 输入(干之前要什么)/ 产出(干完交什么)/ 模板(直接抄)/ DoD(验收门)/ 状态`
> 状态:⚪ 未开始 / 🟡 进行中 / 🟢 完成 / 🔴 阻塞

### M-01 阿里云主账号 access

| 字段 | 内容 |
|---|---|
| Owner | 项目方负责人(本人) |
| 输入 | 主账号手机号 + 实名信息 |
| 产出 | 主账号开通 + 实名认证完成 + 充值预付费余额 ≥ ¥3,000(M4 一月开销估算) |
| 模板 | https://www.aliyun.com/ 注册;企业实名走"企业认证"通道 |
| DoD | 能登录控制台 + 余额可查 + 已开通服务:ECS / RDS / Tair / OSS / SMS / OCR / KMS / ACR |
| 状态 | ⚪ |

---

### M-02 工程师子账号 + RAM 策略

| 字段 | 内容 |
|---|---|
| Owner | 项目方 ops |
| 输入 | M-01 完成 + 工程师姓名清单(tech lead / backend × N) |
| 产出 | 每位工程师独立 RAM 用户 + 启用 MFA + 仅必要权限 |
| 模板 | 见本文 §3 RAM 策略 JSON 模板 |
| DoD | 工程师能 `aliyun configure` 登录 + 跑 `aliyun ecs DescribeInstances` 返自家可见列表 + 试越权(读他人 bucket)返 403 |
| 状态 | ⚪ |

---

### M-03 Azure 订阅 + OpenAI 资源 ownership

| 字段 | 内容 |
|---|---|
| Owner | 项目方负责人 + AI 工程接口人 |
| 输入 | Azure 账号 + 信用卡(或企业协议)+ 申请 OpenAI Service 准入(通过率视区域/用途,**HK 区域通常 1-2 周**) |
| 产出 | Resource Group `yaoqi-prod-hk` + `yaoqi-staging-hk` + Cognitive Service `yaoqi-aoai-hk` + 至少 1 个 deployment(没有微调先建 `gpt-4o-mini`)+ 主 key + 备 key |
| 模板 | 见本文 §7 Azure OpenAI 申请要点 |
| DoD | `curl -H "api-key: $KEY" "$ENDPOINT/openai/deployments?api-version=2024-10-21"` 返 200 + 列表至少 1 项 + quota ≥ 30k TPM |
| 状态 | ⚪ |

---

### ~~M-04 域名 + ICP 备案 ⚠️ 关键路径最长~~ **已废弃 2026-05-26**

> **决议**:网站前端部署在香港节点(非境内服务器),工信部 ICP 备案要求只针对"接入境内服务器的网站",故 M-04 整张卡作废。
> **替代**:见 [M-13 HK 前端节点选型 + 域名 DNS 接管](#m-13-hk-前端节点选型--域名-dns-接管新增)
> **历史保留**:§5 ICP 备案材料清单仍保留作为知识参考(他日若改回境内部署可复用),但状态置 N/A。

| 字段 | 内容 |
|---|---|
| Owner | ~~项目方负责人 + 法务~~ |
| 状态 | 🚫 已废弃(replaced by M-13) |

---

### M-05 阿里云短信签名审核

| 字段 | 内容 |
|---|---|
| Owner | 项目方 ops |
| 输入 | 公司名称 / 品牌 "曜齐" 商标证 或 域名备案 |
| 产出 | 签名 "曜齐" 审核通过(状态:已通过)|
| 模板 | 见本文 §6 短信签名申请文案 |
| DoD | 短信控制台签名列表显示"审核状态:已通过" |
| 状态 | ⚪ |
| 风险 | 审核 1-3 天;首次拒可改文案重提 |

---

### M-06 短信模板审核

| 字段 | 内容 |
|---|---|
| Owner | 项目方 ops |
| 输入 | M-05 完成 |
| 产出 | 2 套模板:`SMS_LOGIN`(登录验证码) + `SMS_NOTIFY`(通知,P1)审核通过 |
| 模板 | 见本文 §6 短信模板申请文案 |
| DoD | 模板 ID 可填进 `.env`(`ALIYUN_SMS_TEMPLATE_LOGIN=SMS_xxxxxxxx`)+ 测试发送成功 |
| 状态 | ⚪ |

---

### M-07 OSS Bucket 创建

| 字段 | 内容 |
|---|---|
| Owner | 项目方 ops + tech lead |
| 输入 | M-01 完成 + 区域选定(华东 1 杭州,与 ECS 同区) |
| 产出 | Bucket `yaoqi-prod` + `yaoqi-staging` 创建;**ACL = private**;SSE-KMS 加密;生命周期规则;跨区域复制(prod) |
| 模板 | 控制台创建,关键设置:ACL=私有 / 存储类型=标准 / 区域=oss-cn-hangzhou / 加密=KMS(M-09 CMK) |
| DoD | `aliyun oss bucket-info yaoqi-prod` 返 `ACL: private` + 加密=KMS;[Security-Checklist C-01](../Backend-Security-Checklist_v0.1.md) 通过 |
| 状态 | ⚪ |

---

### M-08 私调 Azure deployment 名(可选)

| 字段 | 内容 |
|---|---|
| Owner | AI 工程方 |
| 输入 | M-03 完成 + 微调训练数据 + Azure OpenAI Studio 准入 |
| 产出 | Deployment `aoai-private-report` 发布;名字填进 `AOAI_DEPLOYMENT_REPORT` |
| 模板 | Azure OpenAI Studio → Fine-tuning → 选基座(`gpt-4o-mini` / `gpt-4o`) → 上传训练集 → 训练完发布为 deployment |
| DoD | API 调用 deployment 返回结构化 JSON;不上线前用 `gpt-4o-mini` 顶 |
| 状态 | ⚪(M4 不卡;由 AI 工程那一脚承接) |

---

### M-09 KMS CMK + Secret 入库

| 字段 | 内容 |
|---|---|
| Owner | 项目方 ops + DevOps |
| 输入 | M-01 完成 |
| 产出 | KMS CMK 创建;所有 secret(DB / Redis / JWT / OSS AK/SK / OCR / SMS / Azure key)入 KMS 凭据管家 |
| 模板 | 见本文 §4 KMS Secret 命名规范 |
| DoD | `aliyun kms get-secret-value --secret-name yaoqi/prod/database-url` 返密文解密成功;权限 grant 给 `yq-deploy` 子账号 |
| 状态 | ⚪ |

---

### M-10 真实玉石 / 珠宝样本

| 字段 | 内容 |
|---|---|
| Owner | 业务方专家 |
| 输入 | 真实购买 / 鉴定经历 |
| 产出 | 至少 **20 个完整样本**:多角度图片(自然光 / 强光 / 背光 / 细节) + 证书扫描件 + 鉴定报告文本 + 价格区间 + 处理风险标注 |
| 模板 | 见本文 §8 样本收集模板 |
| DoD | 数据进 OSS `samples/` 目录 + 元数据进 `samples-metadata.csv`;能跑 staging 完整 OCR + 报告 |
| 状态 | ⚪(滚动收集,不卡 M4 上线但卡 AI 评测) |
| 备注 | 与 Product-Spec §22 待确认项一致;先 5 个跑通,再扩到 20+ |

---

### M-11 监控告警通道

| 字段 | 内容 |
|---|---|
| Owner | 项目方 ops |
| 输入 | M-01 完成 |
| 产出 | 企业微信 / 飞书 / 钉钉 群机器人 webhook + 邮件接收 list + on-call 电话(P0 用) |
| 模板 | 阿里云 CMS → 报警联系人组 → 新增联系组"yaoqi-oncall" → 配 webhook |
| DoD | 触发一次测试告警(CPU > 95% 模拟),通道全部收到 |
| 状态 | ⚪ |

---

### M-12 跳板机 SSH 公钥白名单

| 字段 | 内容 |
|---|---|
| Owner | tech lead |
| 输入 | 工程师公钥(`~/.ssh/id_ed25519.pub`)清单 |
| 产出 | ECS-Jump `~yaoqi/.ssh/authorized_keys` 写入;sshd_config 禁密码、禁 root |
| 模板 | 见本文 §9 SSH 配置模板 |
| DoD | 工程师从自家终端 `ssh yaoqi@<jump-ip>` 进得去 + 密码登录 + root 登录都被拒 |
| 状态 | ⚪ |

---

### M-13 HK 前端节点选型 + 域名 DNS 接管(新增 2026-05-26,替代 M-04)

| 字段 | 内容 |
|---|---|
| Owner | 项目方负责人 + tech lead |
| 输入 | 域名(可在境外或境内注册商购买,**无需 ICP**)+ HK 节点供应商选定 |
| 产出 | (1) 域名所有权 + DNS 接管(指向 HK 节点);(2) HK 前端节点选定并部署 Next.js;(3) 后端 SLB 加 CORS 白名单允许 HK 前端域名;(4) 端到端 P95 < 800ms 验证报告 |
| 模板 | HK 节点候选(按优先级):**Vercel Hong Kong / Singapore edge**(推荐,Next.js 原生,部署 1 小时;**注意自动 SSL + 与 Next.js 15 RSC 适配最好**) / **阿里云国际站 HK Region ECS**(与华东后端同账号,网络互通好查;但要自管 Nginx / SSL)/ **Cloudflare Pages HK PoP**(免费但 SSR 支持弱) |
| DoD | (1) `dig yaoqi.<host>` 返 HK 节点 IP;(2) `curl https://yaoqi.<host>/` 200 + 内容由 HK 节点出;(3) 后端 `Access-Control-Allow-Origin` 白名单含前端域名;(4) HK 用户端到端 API 调用 P95 < 800ms |
| 状态 | ⚪(替代 M-04;1-3 天 lead time)|
| 风险 | (1) Vercel 在大陆访问质量波动,需测真实大陆用户体验;(2) 前后端跨境 RTT(80-150ms)叠加 LLM 链路可能导致总耗时偏高,Stage 4 上线前必跑端到端压测;(3) Cookie SameSite=None + Secure 强制 HTTPS,会撞 staging http 调试;(4) 阿里云华东后端 SLB 出公网带宽费用 — 估算月度成本(预计 < ¥200);(5) 若涉及"金融 / 经营性"信息服务,香港个人数据条例(PDPO)也有合规义务,法务复核 |

---

## 3. RAM 子账号策略 JSON 模板(M-02)

> 给阿里云 RAM 控制台 → 权限策略 → 新建。**最小权限**原则,工程师只能读 ECS / 推 ACR / 管 staging DB。

### 3.1 `yq-engineer`(工程师日常)

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:Describe*",
        "ecs:GetConsoleOutput",
        "rds:Describe*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["cr:PushRepository", "cr:PullRepository", "cr:Get*", "cr:List*"],
      "Resource": "acs:cr:*:*:repository/yaoqi/*"
    },
    {
      "Effect": "Allow",
      "Action": ["oss:GetObject", "oss:ListObjects"],
      "Resource": "acs:oss:*:*:yaoqi-staging/*"
    },
    {
      "Effect": "Deny",
      "Action": ["oss:*"],
      "Resource": "acs:oss:*:*:yaoqi-prod*"
    }
  ]
}
```

### 3.2 `yq-deploy`(CI/CD 部署专用)

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["cr:PullRepository"],
      "Resource": "acs:cr:*:*:repository/yaoqi/*"
    },
    {
      "Effect": "Allow",
      "Action": ["kms:GetSecretValue", "kms:Decrypt"],
      "Resource": "acs:kms:*:*:secret/yaoqi/*"
    },
    {
      "Effect": "Allow",
      "Action": ["ecs:RunCommand", "ecs:InvokeCommand"],
      "Resource": "acs:ecs:*:*:instance/<ecs-api-id-1>,acs:ecs:*:*:instance/<ecs-api-id-2>"
    }
  ]
}
```

### 3.3 `yq-app-oss`(运行时 OSS access)

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "oss:PutObject", "oss:GetObject", "oss:DeleteObject",
        "oss:ListObjects", "oss:GetBucketAcl"
      ],
      "Resource": [
        "acs:oss:*:*:yaoqi-prod",
        "acs:oss:*:*:yaoqi-prod/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["sts:AssumeRole"],
      "Resource": "*"
    }
  ]
}
```

类似为 `yq-app-ocr` / `yq-app-sms` / `yq-migrate`(DDL 专用)各开一份;遵循[Deployment Guide §2.5](../Backend-Deployment-Guide_v0.1.md) 表。

### 3.4 RAM 红线

- ⚠️ 任何子账号**禁止**挂 `AdministratorAccess`
- ⚠️ 子账号**强制 MFA**(RAM 设置 → 必须 MFA)
- ⚠️ AccessKey 季度轮换;离职 24h 内禁用

---

## 4. KMS Secret 命名规范(M-09)

```text
yaoqi/<env>/<secret-name>

环境:
  - staging
  - prod

Secret 列表:
  yaoqi/prod/database-url
  yaoqi/prod/redis-url
  yaoqi/prod/jwt-secret
  yaoqi/prod/aliyun-oss-ak
  yaoqi/prod/aliyun-oss-sk
  yaoqi/prod/aliyun-ocr-ak
  yaoqi/prod/aliyun-ocr-sk
  yaoqi/prod/aliyun-sms-ak
  yaoqi/prod/aliyun-sms-sk
  yaoqi/prod/aoai-api-key
  yaoqi/prod/aoai-endpoint
  yaoqi/prod/aoai-deployment-report
  yaoqi/prod/aoai-deployment-ocr
  yaoqi/prod/aoai-deployment-image-summary
  yaoqi/prod/aoai-deployment-embedding
```

**轮换周期**:
- DB / Redis / OSS AK : 季度
- Azure key: **月度**(跨云风险)
- JWT_SECRET: 季度;轮换会让所有 session 失效,需配通知

**红线**:
- 一个 secret 一个 KMS entry,不要塞 `.env` 整段进一个 secret
- staging 与 prod **不共用** secret(否则 staging 出事可能横向到 prod)

---

## 5. ICP 备案材料清单(原 M-04,**2026-05-26 已废弃**)

> 🚫 **本节已废弃**:决议改走 HK 前端节点(见 M-13),工信部 ICP 备案不再需要。
> 本节保留作为知识参考,他日若改回境内服务器部署可复用;**当前 prod 不走本节流程**。
>
> ~~走**阿里云 ICP 代备案系统**;主体备案 + 网站备案两步走。~~

### 5.1 主体材料(企业)

| # | 材料 | 形式 |
|---|---|---|
| 1 | 营业执照 | 扫描件 / 拍照(清晰、四角完整) |
| 2 | 法定代表人身份证 | 正反面扫描 |
| 3 | 主体负责人手机号 | 接审核电话(管局可能回电) |
| 4 | 主体负责人邮箱 | 接审核邮件 |
| 5 | 公司公章 | 用于盖《信息安全管理协议》 |
| 6 | 公司通信地址 | 营业执照一致 |

### 5.2 网站材料

| # | 字段 | 取值示例 |
|---|---|---|
| 1 | 域名 | `yaoqi.com`(必须企业主体名下购买) |
| 2 | 网站名称 | "曜齐玉石珠宝鉴定估价助手" |
| 3 | 网站负责人 | 同 5.1 #3(或另设) |
| 4 | 网站服务内容 | "AI 辅助玉石珠宝鉴定与估价信息服务"(不要写"电商"/"在线交易"会要前置审批) |
| 5 | 服务器接入商 | 阿里云(自动填) |
| 6 | 服务器节点 | 与购买的 ECS 区域一致 |

### 5.3 关键风险

- ⚠️ **域名所有人 = 备案主体**(企业);个人买的域名走不通企业备案
- ⚠️ 部分省份要"主体负责人核验视频"(配合阿里云 APP 拍)
- ⚠️ 若涉及"鉴定结论对外发布",可能被管局认定需**经营性 ICP** — 提前与法务对齐定性
- ⚠️ 备案期间**不能**访问;先开发用临时域名 + Cloudflare 等海外节点过渡

### 5.4 时间线

```
T-30  提交主体材料
T-28  阿里云初审(1-2 天)
T-26  提交至当地管局
T-7   管局审核(7-20 天因省而异)
T-0   备案成功 + 备案号下发
```

---

## 6. 短信签名 + 模板申请文案(M-05/M-06)

### 6.1 签名申请

| 字段 | 取值 |
|---|---|
| 签名名称 | `曜齐`(纯品牌字,审核率高) |
| 适用场景 | 通用 |
| 签名来源 | "企事业单位的全称或简称" |
| 证明文件 | 营业执照 + "曜齐"商标证(若有)/ 公司官网链接(HK 节点也可)— 阿里云短信签名审核要求"可证明品牌归属",原 ICP 备案截图选项已无,改提交商标证或公司官网截图 |
| 申请说明文案 | "曜齐 YAOQI 为本公司旗下玉石珠宝鉴定估价 AI 辅助产品的品牌名称,与公司主体一致,用于向注册用户下发账户登录验证码与系统通知。" |

### 6.2 模板申请

**SMS_LOGIN(验证码)**

| 字段 | 取值 |
|---|---|
| 模板名称 | 曜齐-登录验证码 |
| 模板类型 | 验证码 |
| 模板内容 | `您的验证码为 ${code},5 分钟内有效。请勿向他人泄漏,曜齐不会主动索取此验证码。` |
| 申请说明 | "用户在曜齐玉石珠宝鉴定估价助手注册 / 登录时,系统下发的一次性 6 位数字验证码,5 分钟内有效。" |

**SMS_NOTIFY(通知,P1)**

| 字段 | 取值 |
|---|---|
| 模板名称 | 曜齐-报告就绪通知 |
| 模板类型 | 通知 |
| 模板内容 | `您的案例 ${case_no} 鉴定报告已就绪,请登录曜齐 APP / 网页查看。` |
| 申请说明 | "用户提交鉴定案例后,系统异步生成 AI 报告,完成后下发通知,引导回 APP / 网页查看。" |

**关键风险**:
- ⚠️ "鉴定"字眼可能被审核认为夸大 — 备选文案:"AI 分析报告已就绪"
- ⚠️ 首次模板拒可改文案重提,与签名独立

---

## 7. Azure OpenAI 资源申请要点(M-03)

### 7.1 准入申请(必须)

- Azure OpenAI Service **不是默认开通**,需走"Limited Access Form"
- 表单(2026 年版)填:
  - 公司信息(英文)
  - 用例描述:"AI-assisted jewelry & jade appraisal report generation, with structured output schema and human review workflow"
  - 数据是否含 PII:**No**(在 prompt 层清洗,见 [ai-integration-engineer §禁止11](../../skills/ai-integration-engineer.md))
  - 预期 TPM:`Report 30k / Embedding 100k`
- **HK 区域通常 1-2 周**回复;通过后可在 Studio 建 deployment

### 7.2 Resource Group / 资源拓扑

```
Subscription: Pay-As-You-Go(或企业协议 EA)
├─ Resource Group: yaoqi-prod-hk
│  └─ Cognitive Service: yaoqi-aoai-hk-prod
│     ├─ Deployment: aoai-private-report          (gpt-4o-mini 初期)
│     ├─ Deployment: aoai-deployment-ocr-correct  (gpt-4o-mini)
│     ├─ Deployment: aoai-deployment-image-summary(gpt-4o)
│     └─ Deployment: aoai-text-embedding-3-small  (text-embedding-3-small)
└─ Resource Group: yaoqi-staging-hk
   └─ Cognitive Service: yaoqi-aoai-hk-staging
      └─ (同上 4 个 deployment,quota 减半)
```

### 7.3 Quota 申请

默认 quota 通常很小(几 k TPM);上线前**主动提工单**申请:
- Report deployment: ≥ 30k TPM
- Embedding deployment: ≥ 100k TPM
- 图片摘要 deployment: ≥ 10k TPM

申请理由:"Production traffic for jewelry appraisal SaaS, estimated 500 reports/day with 4k token avg = 60k tokens/day baseline, 5x peak."

### 7.4 私调

- Azure OpenAI Studio → Fine-tuning
- 基座选 `gpt-4o-mini` 起步(便宜、训练快)
- 训练数据 JSONL 格式(messages 数组)
- 微调成本: ~$25/1M training tokens(具体看 Azure 当期定价)

---

## 8. 真实样本数据收集模板(M-10)

### 8.1 单样本目录结构

```
samples/
└─ YQ-SAMPLE-001-feicui-shouzhuo/
   ├─ images/
   │  ├─ natural-light-front.jpg
   │  ├─ natural-light-back.jpg
   │  ├─ strong-light-1.jpg
   │  ├─ strong-light-2.jpg
   │  ├─ backlight.jpg
   │  └─ detail-1.jpg ~ detail-N.jpg
   ├─ certificate/
   │  └─ ngtc-cert.jpg
   ├─ ground-truth.json
   └─ notes.md
```

### 8.2 `ground-truth.json` 模板

```json
{
  "sample_id": "YQ-SAMPLE-001",
  "category": "翡翠手镯",
  "sub_category": "圆条素镯",
  "size": { "diameter_mm": 58, "width_mm": 12, "thickness_mm": 8 },
  "weight_g": 52.3,
  "certificate": {
    "org": "NGTC",
    "no": "Z1234567",
    "result": "翡翠(A 货)"
  },
  "expert_judgment": {
    "material_hint": "翡翠 A 货",
    "process_risk": [],
    "species_water": "糯种,飘绿",
    "quality_level": "中档",
    "price_range_cents": [800000, 1500000],
    "recycle_price_cents": [400000, 700000],
    "liquidity": "medium",
    "need_reinspect": false,
    "risk_level": "low"
  },
  "context": {
    "purchase_channel": "线下店",
    "purchase_price_cents": 1200000,
    "purchase_date": "2024-08"
  },
  "annotator": "<专家姓名>",
  "annotated_at": "2026-05-XX"
}
```

### 8.3 样本数量目标

| 阶段 | 数量 | 用途 |
|---|---|---|
| Staging smoke | 5 | 跑通 OCR + 报告链路 |
| AI 评测 v1 | 20 | `evals/datasets/jade_golden_set.json` 初始 |
| AI 评测 v2(P1) | 100 | RAG 召回池有意义 |

### 8.4 收集纪律

- ⚠️ **不收 PII**:不要把买家 / 卖家姓名 / 联系方式入样本
- ⚠️ 证书带个人信息的部分**马赛克**
- ⚠️ 样本归属业务方;工程方仅用于评测,不外传
- ⚠️ 每月新增样本归档 `samples-YYYY-MM.tar.gz`,上 OSS 私有桶

---

## 9. SSH 跳板机配置模板(M-12)

### 9.1 `sshd_config`(`/etc/ssh/sshd_config`)

```
Port 22
PermitRootLogin no
PasswordAuthentication no
ChallengeResponseAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
MaxAuthTries 3
LoginGraceTime 30
AllowUsers yaoqi
ClientAliveInterval 300
ClientAliveCountMax 2
Protocol 2
X11Forwarding no
```

### 9.2 跳板机操作

```bash
# 创建运维用户(不开 root)
sudo useradd -m -s /bin/bash yaoqi
sudo mkdir -p /home/yaoqi/.ssh
sudo chmod 700 /home/yaoqi/.ssh

# 把工程师公钥逐行 append
sudo tee -a /home/yaoqi/.ssh/authorized_keys <<'EOF'
ssh-ed25519 AAAA... mgong@yaoqi-tech-lead
ssh-ed25519 AAAA... eng2@yaoqi-backend
EOF

sudo chmod 600 /home/yaoqi/.ssh/authorized_keys
sudo chown -R yaoqi:yaoqi /home/yaoqi/.ssh
sudo systemctl restart sshd
```

### 9.3 验证

```bash
# 工程师本地
ssh yaoqi@<jump-public-ip>                                # 应该进得去
ssh root@<jump-public-ip>                                  # 应该被拒
ssh -o PreferredAuthentications=password yaoqi@<jump-ip>   # 应该被拒
```

---

## 10. 周会 status 模板

每周一上午 10:00 sync,15 分钟内过完:

```text
| 物料 | 状态 | 上周进展 | 本周计划 | 阻塞 |
|---|---|---|---|---|
| M-01 阿里云主账号 | 🟢 | 完成实名 | — | — |
| ~~M-04 域名+ICP~~ | 🚫 废弃 | 改走 HK 前端(M-13)| 无需备案 | — |
| M-13 HK 前端节点 | 🟡 | 选定 Vercel HK | 部署 + DNS 接管 | — |
| M-05 短信签名 | 🟡 | 提交"曜齐" | 等审核 | — |
| ... | ... | ... | ... | ... |
```

阻塞项 → 同步抬升到 [tracker §二](./M4-backend-rollout-tracker.md) 对应未决项;每项有责任人 + 期望解决时间。

---

## 11. 与 tracker 对齐

| tracker 项 | 本文卡片 |
|---|---|
| §2.4 阿里云子账号 | M-01 / M-02 |
| §2.4 Azure ownership | M-03 |
| ~~§2.4 域名 + ICP~~ | ~~M-04~~(已废弃 2026-05-26)|
| §2.4 域名 + HK 前端节点 | M-13(新增,替代 M-04)|
| §2.4 短信签名/模板 | M-05 / M-06 |
| §2.4 OSS Bucket | M-07 |
| §2.4 私调 deployment | M-08 |
| (Deployment Guide §4 #11) 告警通道 | M-11 |
| (Deployment Guide §4 #12) 跳板机公钥 | M-12 |
| §2.4 真实样本 | M-10 |
| (新增) KMS CMK | M-09 |

物料全部 🟢 后,**M4 实施可以开工**(对应 tracker §二 中 §2.1 的"进入 M4 实施"路径)。

---

## 维护规则

1. 每周一更新 §2 各卡的"状态"列
2. 新增物料 → 加 M-13 / M-14 卡片,本文 §1 时间线同步
3. 物料全 🟢 后,本文移到 `docs/audit/m4-materials-collected-YYYY-MM.md` 归档,tracker §2.4 标完成
4. 任何模板(RAM JSON / KMS 命名 / 短信文案)与实际申请有差 → 改本文,不改其它文档(本文是模板权威源)
