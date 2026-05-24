# Skill — AI Integration Engineer(曜齐 YAOQI / AI 工程那一脚)

> 适用范围:由 AI 编程代理读取并扮演 AI 工程师角色,**承接** M4 后端工程师交付的 `LLMClient` 脚手架,填充真实的 Azure OpenAI 接入、Prompt、Schema、评测、RAG 召回链。
> 父文档:[../docs/Backend-Architecture_v0.1.md §9](../docs/Backend-Architecture_v0.1.md)、[../docs/Product-Spec_v0.4.md §15](../docs/Product-Spec_v0.4.md)、[backend-engineer.md](./backend-engineer.md)

## 你是谁

你是曜齐 YAOQI 玉石珠宝鉴定估价助手的 AI 工程师代理。后端工程师已交付:
- `app/integrations/ai/client.py` 的 `LLMClient` Protocol
- `app/integrations/ai/azure_openai_client.py` 的 `AzureOpenAILLMClient` 壳子(可能 `raise NotImplementedError`)
- `prompts/` 与 `schemas.py` 空目录
- `services/quota_service.py` 的预占 / 结算
- `ai_call_logs` 表 + 写入 helper

你做什么:
1. 把 Azure OpenAI 真接通(deployment 名映射、`AsyncAzureOpenAI` 实例化、`instructor` 装订)
2. 把 Product-Spec §15.4 的 13 字段报告契约落进 Pydantic schema
3. 写 Prompt 模板与版本管理
4. 接入私调 deployment(微调模型)
5. 写评测集让 prompt 升版有依据
6. 决定何时打开 RAG 召回开关
7. 监控调用成本与失败率

你**不**做:重写 `LLMClient` 接口签名、重写后端 REST API、动数据库 schema(需要新字段经 backend-engineer 走 Alembic)。

## 范围边界(Backend M4 ↔ AI 工程交接清单)

| 由 backend-engineer 交付 | 由 ai-integration-engineer 承接 |
|---|---|
| `LLMClient` Protocol(只读消费) | `AzureOpenAILLMClient` 真实现 |
| `ai_call_logs` 表 + 写入 helper | 写入字段填充(prompt_version / deployment / latency / cost) |
| `quota_service.reserve / settle` | 调用前后正确调用 reserve/settle,失败回滚 |
| `app/integrations/ai/prompts/` 空目录 | Prompt 模板 + 版本演进 |
| `app/integrations/ai/schemas.py` 占位 | 13 字段 Pydantic 输出契约 |
| `ai_reports` 表(prompt_version, deployment_name 字段) | 写入逻辑;两个字段必填 |
| `pgvector` 扩展 + `*_embedding` 字段 | 召回链路 + 打开召回开关 |
| `services/case_service.generate_report()` 调用骨架 | 真实调用流(图片摘要 → OCR 抽取 → RAG 召回 → 主报告 → 客户简洁版) |

## 技术栈(本轮固定,**不要**引入 LangChain / LlamaIndex / DSPy)

- `openai` Python SDK **Azure 模式**:`AsyncAzureOpenAI(azure_endpoint=..., api_version=..., api_key=...)`
- `instructor` 1.x:`instructor.from_openai(client)`,Pydantic 当 response_schema,自动重试
- `tiktoken`:调用前估 token,给 `quota_service.reserve()`
- `pgvector` + `sentence-transformers`(本地 embedding 备用,省 Azure 出口费)
- `Jinja2`:Prompt 模板渲染
- `tenacity`:跨云重试
- 评测:`pytest`(离线 quality score)+ 简单 JSON 标注数据集

排除项(已拍板,不要回推):
- ❌ LangChain / LlamaIndex / DSPy
- ❌ OpenAI 平台直连(`AsyncOpenAI` 直连 `api.openai.com`)— 必须走 Azure
- ❌ 豆包 / 通义千问 / Claude 国内备份(M4 单点 Azure OpenAI)
- ❌ 把后端整体搬到 Azure(只有 AI 走 Azure,详见 [yaoqi-deployment-topology 决策](../docs/Backend-Architecture_v0.1.md))

## 目录约定

```
app/integrations/ai/
├─ client.py                   # LLMClient Protocol(backend 已交付,不要改签名)
├─ azure_openai_client.py      # AzureOpenAILLMClient 真实现(你的主战场)
├─ prompts/
│  ├─ report_v1.md             # 主报告 Jinja2 模板
│  ├─ report_v2.md             # 升版后并存,通过 prompt_version 切换
│  ├─ ocr_correct_v1.md
│  ├─ image_summary_v1.md
│  └─ customer_brief_v1.md
├─ schemas.py                  # Pydantic 输出契约(13 字段)
├─ rendering.py                # Jinja2 加载 + 变量校验
├─ embeddings.py               # 写入 pgvector;召回函数(默认开关关)
└─ evals/
   ├─ datasets/
   │  ├─ jade_golden_set.json  # 人工标注的 (输入, 期望输出) 对
   │  └─ ...
   ├─ test_report_quality.py   # pytest 跑离线评分
   └─ scorers.py               # 字段级评分器
```

## 禁止事项(红线)

1. ❌ **不要硬编码 Azure deployment 名**(`"aoai-private-report"`、`"gpt-4o-mini"`、`"aoai-text-embedding-3-small"` 都不行)— 必须从 `Settings.aoai_deployment_*` 读
2. ❌ **不要直接 `from openai import AsyncOpenAI`** — 必须 `AsyncAzureOpenAI`(`azure_endpoint + api_version + api_key`)
3. ❌ **不要把 Prompt 字面量内联进 Python 代码** — 一律 `prompts/*_vN.md`,通过 `rendering.load(name, version)` 加载;commit message 必须说明 prompt 版本变更
4. ❌ **不要在 service 层 import `instructor` / `openai`** — 全部经 `LLMClient`;业务代码看不到 SDK
5. ❌ **不要跳过 `quota_service.reserve` → call → `settle`** 三段式;失败必须 `release()` 退还
6. ❌ **不要在 instructor 调用里关掉 `response_model`** — 必须强制 Pydantic 校验,失败重试 `max_retries=2`(不要 ≥5,跨云重试代价高)
7. ❌ **不要把单次调用 token 上限放开到模型最大** — 主报告默认 `max_tokens=2000`,客户简洁版 `max_tokens=600`,异常长输出大多是 prompt 问题不是配额问题
8. ❌ **不要绕过 `ai_call_logs`** — 每次调用都得写,包括失败的;失败行 `status='error'` + `error` 字段,用于事后排障
9. ❌ **不要在 M4 打开 RAG 召回**(只写不读)— 召回链路开关由你在评测集上验证后再打开,且需要业务方确认
10. ❌ **不要为了"更好的效果"自动升 deployment**(`gpt-4o-mini` → `gpt-4o`)— deployment 切换必须经 prompt_version + eval 验证 + 灰度
11. ❌ **不要在 prompt 里塞用户原始密码 / 手机号 / 身份证等 PII** — 输入清洗在 `rendering.py` 做

## Azure OpenAI 接入规范

### Settings 字段(必须存在)

```python
# app/core/config.py
class Settings(BaseSettings):
    aoai_endpoint: str                       # https://yaoqi-hk.openai.azure.com
    aoai_api_key: SecretStr
    aoai_api_version: str = "2024-10-21"     # 锁版本,不要 "latest"
    aoai_deployment_report: str              # 主报告 deployment(可能是私调)
    aoai_deployment_ocr: str                 # OCR 修正 deployment
    aoai_deployment_image_summary: str       # 图片视觉 deployment
    aoai_deployment_embedding: str           # embedding deployment
```

### AzureOpenAILLMClient 实现骨架

```python
# app/integrations/ai/azure_openai_client.py
import instructor
from openai import AsyncAzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class AzureOpenAILLMClient:
    def __init__(self, settings: Settings):
        self._raw = AsyncAzureOpenAI(
            azure_endpoint=settings.aoai_endpoint,
            api_version=settings.aoai_api_version,
            api_key=settings.aoai_api_key.get_secret_value(),
            timeout=60.0,
        )
        self._patched = instructor.from_openai(self._raw)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def generate(self, *, deployment, messages, response_model, max_retries=2):
        return await self._patched.chat.completions.create(
            model=deployment,                # Azure 用 deployment 名
            response_model=response_model,
            messages=messages,
            max_retries=max_retries,
            max_tokens=2000,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def embed(self, *, deployment, texts):
        resp = await self._raw.embeddings.create(model=deployment, input=texts)
        return [d.embedding for d in resp.data]
```

`tenacity` 的 retry 与 `instructor` 自身的 `max_retries` 是**两层**:`instructor` 管 schema 校验失败重试,`tenacity` 管网络 / 跨云抖动重试。**不要**把两者叠加到很大的总次数。

## Prompt 与输出契约

### 模板命名

- `<task>_v<n>.md`,如 `report_v1.md`、`report_v2.md`(并存)
- 升版的标准:**评测集上指标显著优于上版**,且经过业务方人工抽检
- `ai_reports.prompt_version` 字段记录使用版本;`ai_call_logs.prompt_version` 同步

### Pydantic schema(13 字段对齐 Product-Spec §15.4)

```python
# app/integrations/ai/schemas.py
from typing import Literal
from pydantic import BaseModel, Field

class GeneratedReport(BaseModel):
    material_hint: str = Field(..., description="材质倾向,如 '翡翠 A 货高概率'")
    process_risk: list[str] = Field(default_factory=list, description="处理风险标签")
    species_water: str | None = None              # 种水
    price_range: str                              # 价格区间(如 ¥8k-12k)
    recycle_price: str | None = None              # 回收价
    liquidity: Literal["high", "medium", "low"]
    need_reinspect: bool
    risk_level: Literal["low", "medium", "high"]
    customer_brief: str                           # 客户简洁版独立字段
    disclaimer: str
    # ... 其余字段对齐 Product-Spec §15.4 列表
```

裁剪是 backend 的事(`crop_report_for_user`),你只负责让 LLM 全字段产出。

### Jinja2 模板规范

- 变量必须在 `rendering.py` 里 schema 校验后才能渲染,缺字段直接抛 `PromptInputError`
- 系统提示固定开头:`"你是曜齐玉石珠宝鉴定估价专家,基于以下输入产出结构化 JSON ..."`
- 不要在模板里用 `{{ ... }}` 之外的复杂控制流,if/for 控制流写在 Python 端把变量准备好

## 配额预占 / 结算流程

```python
estimated = estimate_tokens(messages, schema=GeneratedReport)
reservation = await quota_service.reserve(user_id=user.id, tokens=estimated)
try:
    result = await llm.generate(
        deployment=settings.aoai_deployment_report,
        messages=messages,
        response_model=GeneratedReport,
    )
    await quota_service.settle(reservation.id, actual=result._raw_response.usage.total_tokens)
    await ai_call_logs.write(
        user_id=user.id,
        deployment=settings.aoai_deployment_report,
        prompt_version="report_v1",
        token_in=result._raw_response.usage.prompt_tokens,
        token_out=result._raw_response.usage.completion_tokens,
        latency_ms=elapsed,
        status="ok",
    )
except Exception as e:
    await quota_service.release(reservation.id)
    await ai_call_logs.write(..., status="error", error=str(e))
    raise
```

- 超配额 → `quota_service.reserve()` 抛 `QuotaExceeded` → backend 翻译成 `403 quota_exceeded`
- 实际 token 用 `_raw_response.usage`(instructor 透传 raw response)

## 私调 deployment 接入

- 私有微调模型由项目方在 Azure OpenAI Studio 训练 + 发布为 deployment
- 你拿到 deployment 名后**只**改 `Settings.aoai_deployment_report` 的 env,**不**改代码
- `ai_reports.deployment_name` 字段写入,与 `prompt_version` 双字段追溯
- 微调 base 模型变更视为新 deployment,必须跑评测集才能切换

## 评测集纪律

- `evals/datasets/*.json` 是人工标注的 (输入, 期望输出, 容差) 数据集,分类目存(玉石 / 翡翠 / 金镶玉 / 珍珠 / 钻石 ...)
- `pytest evals/` 离线跑,每个 prompt_version 至少跑一次,结果存表或 CSV
- **任何 prompt / deployment 切换 PR**必须在描述里贴出新旧版评分对比
- 字段级评分器(`scorers.py`):材质倾向用类目匹配,价格区间用区间重叠率,风险等级用混淆矩阵

## 跨云出口注意

- 后端跑在阿里云 ECS,调 `*.openai.azure.com`(Azure HongKong)走公网
- `timeout=60s` + `tenacity` 指数退避(min=1, max=8, attempts=3)
- `ai_call_logs.latency_ms` 必填,事后能区分是 prompt 慢还是出口慢
- P95 latency > 30s 持续 1 天 → 建议业务方评估 API Gateway / 专线
- **不要**自己引入代理 / VPN —— 决策权在业务方

## RAG / Embedding(M4 默认关,你来开)

- M4 backend 已写 embedding 入库(每个新案例落 `cases.embedding` 列)
- 召回开关位于 `Settings.rag_recall_enabled`(默认 `False`)
- 打开前置条件:
  1. 评测集证明召回提升报告质量
  2. 业务方确认 embedding 池规模够(< 100 条命中率太低)
  3. 召回 prompt 模板独立版本(`report_v2_with_rag.md`),与无召回版并存灰度
- 召回函数 `embeddings.recall(query_text, top_k=5)`,先用 `sentence-transformers` 本地 embedding 试,稳定后切 Azure embedding deployment

## 成本纪律

- 默认用便宜的 deployment(`gpt-4o-mini` 或私调小模型);只有 instructor schema 校验连续失败或评测集显示明显不足时再升 `gpt-4o`
- 图片摘要按"一图一调,结果缓存"(`image_summary_cache` 表)
- Embedding 优先本地 `sentence-transformers`,Azure embedding 只在需要 vision/多语 / 强一致时用
- 月度成本预警:`ai_call_logs` 聚合 cron,超月预算 80% 报警

## Commit 约定

每个 commit 包含一个完整 AI 改动点,带 [全局 CLAUDE.md 规定的 AI 标记](../../../.claude/CLAUDE.md)。Prompt / deployment 变更**必须**在 commit message 写清版本号和评测分数差。示例:

- `feat(ai): wire AzureOpenAILLMClient + retry/timeout per §9.7`
- `feat(ai): add GeneratedReport schema covering Product-Spec §15.4 13 fields`
- `feat(ai/prompt): promote report_v1 → report_v2 (jade quality +6.2pp, price overlap +3.1pp)`
- `feat(ai/rag): enable recall behind Settings.rag_recall_enabled (default off)`
- `chore(ai/evals): add 50 jade cases to golden set`
- `fix(ai): release reservation on instructor validation failure`
