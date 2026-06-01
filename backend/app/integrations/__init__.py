"""外部服务集成层 — OSS / OCR / AI / SMS 等第三方 SDK 封装。

业务层(services)只依赖 integrations 暴露的 Protocol / 工厂函数,
不直接 import 具体 SDK(openai / oss2 / alibabacloud-dysmsapi 等)。
"""
