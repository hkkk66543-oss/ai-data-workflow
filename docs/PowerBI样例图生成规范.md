# Power BI 样例图生成规范

## 目标

BI 样例图用于帮助用户理解页面布局、视觉风格和信息层级，不作为精确数据来源。

## 生成方式

优先方式：

- 使用 `scripts/generate_bi_mockups_with_openai.py`。
- 通过环境变量 `OPENAI_API_KEY` 调用 OpenAI Images API。
- 输出 PNG 到 `outputs/bi_mockups/`。

备用方式：

- 生成 `powerbi_notes/image_prompts.md`。
- 用户手动复制提示词到 ChatGPT 图片生成或其他支持 OpenAI Images API 的环境。

## 图片提示词要求

每一页提示词必须基于：

- 当前行业或业务场景。
- 当前 ADS 表。
- 当前真实字段。
- 当前指标口径。
- 页面业务目标。

## 禁止事项

- 不允许用 Python、matplotlib、seaborn 生成 BI 样例图。
- 不允许使用不存在的字段。
- 不允许把样例图当作指标准确值来源。
- 不允许套用与当前项目无关的行业模板。
