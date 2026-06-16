# BI 样例图生成说明

BI 样例图用于帮助理解 Power BI 页面布局，不作为精确数据来源。

## 自动生成

1. 确认 `powerbi_notes/image_prompts.md` 已生成。
2. 在 Windows PowerShell 设置环境变量：

```powershell
$env:OPENAI_API_KEY="你的key"
```

3. 在项目根目录运行：

```powershell
python scripts/generate_bi_mockups_with_openai.py
```

4. 检查 `outputs/bi_mockups/` 是否生成 PNG 文件。

## 备用流程

如果 OpenAI Images API 无法调用，手动复制 `powerbi_notes/image_prompts.md` 中每一页的提示词，到 ChatGPT 图片生成或其他支持 OpenAI Images API 的环境中生成。

## 注意

- 不要把 API Key 写进代码。
- 不要用 Python、matplotlib、seaborn 生成 BI 样例图。
- BI 样例图只做布局参考，精确指标数值写入 `powerbi_notes/page_xxx.md`。
