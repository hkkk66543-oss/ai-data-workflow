-- MySQL 8.0 data quality checks.
-- 请在真实表名和字段名确认后替换占位符。
-- 本文件不预设行业，不在行业未确认前写 GMV、DAU、逾期率等专属指标。

-- 1. 原始表行数校验
-- SELECT 'source_table_name' AS table_name, COUNT(*) AS row_count FROM source_table_name;

-- 2. ODS / DWD / ADS 行数校验
-- SELECT 'ods_table_name' AS layer_table, COUNT(*) AS row_count FROM ods_table_name;
-- SELECT 'dwd_table_name' AS layer_table, COUNT(*) AS row_count FROM dwd_table_name;
-- SELECT 'ads_table_name' AS layer_table, COUNT(*) AS row_count FROM ads_table_name;

-- 3. 主键唯一性校验
-- SELECT primary_key_field, COUNT(*) AS cnt
-- FROM dwd_table_name
-- GROUP BY primary_key_field
-- HAVING COUNT(*) > 1;

-- 4. 外键关联成功率校验
-- SELECT
--   COUNT(*) AS total_rows,
--   SUM(CASE WHEN dim.primary_key_field IS NOT NULL THEN 1 ELSE 0 END) AS matched_rows
-- FROM dwd_fact_table fact
-- LEFT JOIN dwd_dim_table dim
--   ON fact.foreign_key_field = dim.primary_key_field;

-- 5. 缺失值校验
-- SELECT COUNT(*) AS missing_count
-- FROM dwd_table_name
-- WHERE important_field IS NULL;

-- 6. 重复值校验
-- SELECT dedupe_key_field, COUNT(*) AS cnt
-- FROM dwd_table_name
-- GROUP BY dedupe_key_field
-- HAVING COUNT(*) > 1;

-- 7. 金额字段异常校验，适用于存在金额字段的项目
-- SELECT *
-- FROM dwd_table_name
-- WHERE amount_field < 0;

-- 8. 时间字段异常校验
-- SELECT *
-- FROM dwd_table_name
-- WHERE event_time > CURRENT_TIMESTAMP;

-- 9. 核心指标汇总校验
-- SELECT SUM(metric_source_field) AS detail_metric
-- FROM dwd_fact_table;
--
-- SELECT SUM(metric_field) AS ads_metric
-- FROM ads_summary_table;
