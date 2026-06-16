# 01 Context / Data Understanding

目标：理解数据，而不是直接分析。

请扫描 `data/raw/` 中的所有 csv、xlsx、json、sql 文件。

必须完成：

1. 识别文件名、行数、列数、文件大小、编码格式。
2. 读取每张表前 10 行样例数据。
3. 生成字段字典。
4. 检查缺失值、重复值、异常值、乱码、字段类型问题。
5. 推测主键、外键和表关系。
6. 不修改 `data/raw/`。
7. 不虚构字段、数据、结论。

输出：

- `docs/数据字典.md`
- `docs/数据质量报告.md`
- `docs/表关系说明.md`

完成后进入 `prompts/02_domain_identification.md`。
