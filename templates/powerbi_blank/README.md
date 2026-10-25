# Power BI 空白基线

本目录提供 `Blank.pbip` 入口、空白报表和语义模型，供 `scripts/generate_powerbi.py` 自动填充本次 SQL 结果、模型、DAX、主题与页面。使用者无需另建空白工程，也无需先打开本目录的空白入口。

基线保留页面、模型文化与原主题，排除 `.pbi` 本机缓存、`cache.abf` 和 `.platform` 标识。来源为两个空白组件包 `BI模板.Report.zip`、`BI模板.SemanticModel.zip`，已补齐外层 PBIP 和相对引用。

实际使用方法见 [Power BI 自动生成说明](../../docs/PowerBI自动生成说明.md)。生成工程与真实数据按各自项目独立保存，不覆盖本基线。
