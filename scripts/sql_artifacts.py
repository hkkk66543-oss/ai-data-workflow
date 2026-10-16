"""Persist executed SQL snapshots and actual MySQL model metadata."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


def snapshot_sources(root, plan, run_dir):
    source = run_dir / "source"
    files = {}
    for scripts in plan["layers"].values():
        for path, _ in scripts:
            files[str(path.relative_to(root))] = path
    for kind in ("checks", "exports"):
        for path, _, _ in plan[kind]:
            files[str(path.relative_to(root))] = path
    for relative, path in files.items():
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != plan["hashes"][relative]:
            raise ValueError("SQL changed after planning")
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    imports = [{"file": str(path.relative_to(root)), "table": item["table"], "columns": item["columns"],
                "sha256": plan["hashes"][str(path.relative_to(root))]} for path, item in plan["imports"]]
    source.mkdir(exist_ok=True)
    (source / "imports.json").write_text(json.dumps(imports, ensure_ascii=False, indent=2), encoding="utf-8")
    # Keep confirmed business definitions if present; never copy local connection config.
    for name in ("数据字典.md", "指标口径.md", "SQL中英文命名映射表.md", "表关系说明.md"):
        path = root / "docs" / name
        if path.is_file():
            target = source / "docs" / name
            target.parent.mkdir(exist_ok=True)
            target.write_bytes(path.read_bytes())


def rows(conn, sql, params=()):
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        columns = [c[0] for c in cursor.description]
        result = []
        while batch := cursor.fetchmany(1000):
            result.extend(dict(zip(columns, row)) for row in batch)
        return result
    finally:
        cursor.close()


def engine_info(conn):
    result = rows(conn, "SELECT VERSION() AS version, @@version_comment AS version_comment")
    if len(result) != 1 or not result[0]["version"].startswith("8.0.") or "mariadb" in str(result[0]).lower():
        raise ValueError("Server must be real MySQL 8.0")
    return result[0]


def save_model(conn, database, plan, run_dir):
    model = run_dir / "model"
    model.mkdir()
    tables = rows(conn, """SELECT TABLE_NAME AS table_name, TABLE_TYPE AS table_type,
        ENGINE AS engine, TABLE_COMMENT AS comment
        FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s ORDER BY TABLE_NAME""", (database,))
    columns = rows(conn, """SELECT TABLE_NAME AS table_name, COLUMN_NAME AS field_name,
        ORDINAL_POSITION AS position, COLUMN_TYPE AS field_type, IS_NULLABLE AS nullable,
        COLUMN_DEFAULT AS default_value, COLUMN_KEY AS key_type, EXTRA AS extra,
        COLUMN_COMMENT AS comment
        FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = %s ORDER BY TABLE_NAME, ORDINAL_POSITION""", (database,))
    relationships = rows(conn, """SELECT TABLE_NAME AS table_name, COLUMN_NAME AS field_name,
        CONSTRAINT_NAME AS constraint_name, ORDINAL_POSITION AS position,
        REFERENCED_TABLE_NAME AS referenced_table, REFERENCED_COLUMN_NAME AS referenced_field
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY TABLE_NAME, CONSTRAINT_NAME, ORDINAL_POSITION""", (database,))
    source_mapping = {(i["table"], target): {"source_file": str(path.relative_to(run_dir.parents[2])), "source_field": original}
                      for path, i in plan["imports"] for original, target in i["columns"].items()}
    for column in columns:
        column.update(source_mapping.get((column["table_name"], column["field_name"]),
                                         {"source_file": "", "source_field": ""}))
    payload = {"database": database, "tables": tables, "fields": columns,
               "declared_foreign_keys": relationships,
               "lineage_note": "原始字段来源由导入映射提供；加工字段逻辑见 source/sql/。不凭空推断字段血缘或业务关联。"}
    (model / "model.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    headers = ["table_name", "field_name", "position", "field_type", "nullable", "default_value", "key_type", "extra", "comment", "source_file", "source_field"]
    with (model / "fields.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers)
        writer.writeheader()
        writer.writerows(columns)
    ddl = ["-- MySQL 8.0 actual schema; no data. Select/create the target database separately."]
    # Base tables first so view definitions can reference their underlying tables.
    for table in sorted(tables, key=lambda t: t["table_type"] == "VIEW"):
        name = table["table_name"].replace("`", "``")
        cursor = conn.cursor()
        try:
            cursor.execute(f"SHOW CREATE TABLE `{name}`")
            result = cursor.fetchone()
            ddl.append(result[1].rstrip(";") + ";")
        finally:
            cursor.close()
    (model / "schema.sql").write_text("\n\n".join(ddl) + "\n", encoding="utf-8")
    return {"tables": len(tables), "fields": len(columns), "declared_foreign_keys": len(relationships)}


def artifact_manifest(run_dir):
    artifacts = []
    for path in sorted(run_dir.rglob("*")):
        if path.is_file() and path.name not in {"run.json", "manifest.json"}:
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            artifacts.append({"path": str(path.relative_to(run_dir)), "size": path.stat().st_size, "sha256": digest.hexdigest()})
    (run_dir / "manifest.json").write_text(json.dumps(artifacts, ensure_ascii=False, indent=2), encoding="utf-8")
