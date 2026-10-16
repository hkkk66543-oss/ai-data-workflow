# 用户提供的空白 Power BI 基线

来自两个空白组件 ZIP：BI模板.Report.zip、BI模板.SemanticModel.zip。
未附外层 PBIP，本目录补齐 Blank.pbip 并将报表引用改为 ../Blank.SemanticModel。
保留空白页面、模型设置、文化和原主题；排除 .pbi 本机缓存、cache.abf 和 .platform 项目标识。

Blank.pbip 是空白入口，没有数据或报表组件。自动生成器复制该基线，并添加本次 SQL 结果的模型和 PBIR 页面。原始附件不改动。
