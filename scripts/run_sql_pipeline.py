"""Run reviewed project SQL against MySQL; preview unless --execute is supplied."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd
import sqlparse
import yaml

if __package__:
    from .temporary_mysql import TemporaryMySQL, RuntimeUnavailable
    from .sql_artifacts import artifact_manifest, engine_info, save_model, snapshot_sources
else:
    from temporary_mysql import TemporaryMySQL, RuntimeUnavailable
    from sql_artifacts import artifact_manifest, engine_info, save_model, snapshot_sources

ROOT = Path(__file__).resolve().parents[1]
LAYERS = ("01_ods", "02_dwd", "03_ads")
NAME = re.compile(r"^[\w]+$", re.UNICODE)


class PipelineError(Exception):
    pass


def identifier(name):
    if not isinstance(name, str) or not NAME.fullmatch(name) or len(name) > 64:
        raise PipelineError("表、库和字段名只能包含中文、字母、数字、下划线，且不超过 64 字符。")
    return f"`{name}`"


def project_file(root, value, parent=None):
    if not isinstance(value, str):
        raise PipelineError("文件路径必须是字符串。")
    path = (root / value).resolve()
    boundary = (root / parent).resolve() if parent else root.resolve()
    if not path.is_relative_to(boundary) or not path.is_file():
        raise PipelineError(f"文件不存在或不在规定目录中：{value}")
    return path


def statements(path):
    text = path.read_text(encoding="utf-8-sig")
    if re.search(r"^\s*DELIMITER\b", text, re.I | re.M):
        raise PipelineError(f"不支持 DELIMITER/存储过程脚本：{path.name}")
    # Executable comments can hide statements from a preview. Require plain SQL.
    if "/*!" in text:
        raise PipelineError(f"请将 MySQL 可执行注释展开成普通 SQL：{path.name}")
    parts = []
    for part in sqlparse.split(text):
        clean = sqlparse.format(part, strip_comments=True).strip().strip(";").strip()
        if not clean:
            continue
        if re.match(r"^(USE\b|(?:CREATE|DROP|ALTER)\s+(?:DATABASE|SCHEMA)\b)", clean, re.I):
            raise PipelineError(f"库由配置选择，SQL 中不要切换或创建/删除数据库：{path.name}")
        parts.append(clean)
    return parts


def select_only(path):
    parts = statements(path)
    if len(parts) != 1 or not re.match(r"^SELECT\b", parts[0], re.I):
        raise PipelineError(f"校验/导出文件必须只有一条 SELECT：{path.name}")
    return parts[0]


def load_plan(root, config_path):
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise PipelineError("配置必须为 YAML 对象。")
    db = config.setdefault("database", {})
    db.setdefault("mode", "temporary")
    db.setdefault("name", "analysis_run")
    if db["mode"] not in {"temporary", "existing"}:
        raise PipelineError("database.mode 只支持 temporary / existing。")
    identifier(db["name"])
    if db["mode"] == "existing" and (not isinstance(db.get("user"), str) or not db["user"]):
        raise PipelineError("请填写 database.user。")
    if not isinstance(db.get("port", 3306), int):
        raise PipelineError("database.port 必须为整数。")
    if db.get("create_if_missing", False) not in (True, False):
        raise PipelineError("create_if_missing 必须为布尔值。")
    pipeline = config.get("sql_pipeline", {})
    plan = {"layers": {}, "imports": [], "checks": [], "exports": []}
    for layer in LAYERS:
        files = sorted((root / "sql" / layer).glob("*.sql"))
        # Export SELECT files are configured separately and run only after QA.
        export_paths = {str(i.get("sql_file")) for i in pipeline.get("exports", [])}
        scripts = [(p, statements(p)) for p in files if str(p.relative_to(root)) not in export_paths]
        if not scripts or not any(parts for _, parts in scripts):
            raise PipelineError(f"sql/{layer}/ 缺少真实 SQL，不能把空母版当成执行成功。")
        plan["layers"][layer] = scripts
    seen_tables = set()
    for item in pipeline.get("imports", []):
        table = item.get("table")
        identifier(table)
        if table in seen_tables:
            raise PipelineError("一个目标表只能配置一个导入文件。")
        seen_tables.add(table)
        path = project_file(root, item.get("file"), "data/raw")
        if path.suffix.lower() not in {".csv", ".xlsx", ".json"}:
            raise PipelineError("导入仅支持 CSV、XLSX、JSON records 数组。")
        columns = item.get("columns")
        if not isinstance(columns, dict) or not columns:
            raise PipelineError("每个导入项必须明确配置 原始列名:数据库字段名。")
        if len(set(columns.values())) != len(columns):
            raise PipelineError("导入目标字段不能重复。")
        for col in columns.values():
            identifier(col)
        plan["imports"].append((path, item))
    for kind in ("checks", "exports"):
        items = pipeline.get(kind, [])
        if not items:
            raise PipelineError(f"请配置 sql_pipeline.{kind}，不能跳过业务校验或交付表。")
        seen = set()
        for item in items:
            name = item.get("name")
            identifier(name)
            if name in seen:
                raise PipelineError(f"{kind} 中名称重复。")
            seen.add(name)
            parent = "sql/04_checks" if kind == "checks" else "sql"
            path = project_file(root, item.get("sql_file"), parent)
            query = select_only(path)
            if kind == "checks" and item.get("expect") not in {"zero_rows", "scalar_equals"}:
                raise PipelineError("校验 expect 只支持 zero_rows / scalar_equals。")
            if kind == "checks" and item["expect"] == "scalar_equals" and "value" not in item:
                raise PipelineError("scalar_equals 必须配置 value。")
            plan[kind].append((path, query, item))
    # Snapshot every SQL and raw file to detect edits between preview and execution.
    files = {p for scripts in plan["layers"].values() for p, _ in scripts}
    files.update(p for p, _ in plan["imports"])
    files.update(p for k in ("checks", "exports") for p, _, _ in plan[k])
    files.add(config_path)
    plan["hashes"] = {str(p.relative_to(root)): file_hash(p) for p in sorted(files)}
    return config, plan


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def drain(cursor):
    count = 0
    if cursor.description:
        while rows := cursor.fetchmany(1000):
            count += len(rows)
    while cursor.nextset():
        if cursor.description:
            while cursor.fetchmany(1000):
                pass
    return count


def run_layers(conn, scripts, root, events):
    for path, parts in scripts:
        for number, sql in enumerate(parts, 1):
            event = {"step": "sql", "file": str(path.relative_to(root)), "statement": number}
            events.append(event)
            start = time.monotonic()
            cursor = conn.cursor()
            try:
                cursor.execute(sql)
                drain(cursor)
                conn.commit()
                event["status"] = "passed"
            finally:
                event["seconds"] = round(time.monotonic() - start, 3)
                cursor.close()


def frames(path, item, batch_size):
    if path.suffix.lower() == ".csv":
        # Strings preserve identifiers such as 00123; types are set by ODS schema.
        yield from pd.read_csv(path, dtype=str, keep_default_na=False,
                               encoding=item.get("encoding", "utf-8-sig"),
                               sep=item.get("delimiter", ","), chunksize=batch_size)
    elif path.suffix.lower() == ".xlsx":
        yield pd.read_excel(path, sheet_name=item.get("sheet", 0), dtype=str,
                            keep_default_na=False)
    else:
        raw = json.loads(path.read_text(encoding=item.get("encoding", "utf-8-sig")))
        if not isinstance(raw, list) or any(not isinstance(row, dict) for row in raw):
            raise PipelineError("JSON 必须是对象组成的 records 数组。")
        yield pd.DataFrame(raw)


def insert_batch(cursor, sql, rows):
    cursor.executemany(sql, rows)
    # Read diagnostics explicitly: never emit driver warning text with raw values.
    cursor.execute("SHOW COUNT(*) WARNINGS")
    warning_count = cursor.fetchone()[0]
    drain(cursor)
    if warning_count:
        raise PipelineError("导入产生 MySQL 警告（可能有类型转换/截断），已停止；请检查字段类型与原始数据。")


def import_data(conn, path, item, batch_size):
    table = identifier(item["table"])
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        before = cursor.fetchone()[0]
        drain(cursor)
        if before:
            raise PipelineError(f"目标原始表 {item['table']} 已有数据，停止重复导入；请使用新的项目数据库或审核清理方案。")
        mapping = item["columns"]
        sql = f"INSERT INTO {table} ({','.join(identifier(c) for c in mapping.values())}) VALUES ({','.join(['%s'] * len(mapping))})"
        count = 0
        nulls = item.get("null_values", [""])
        for frame in frames(path, item, batch_size):
            if not set(mapping).issubset(frame.columns):
                raise PipelineError(f"导入文件 {path.name} 缺少配置列。")
            rows = []
            for row in frame[list(mapping)].itertuples(index=False, name=None):
                values = []
                for value in row:
                    if isinstance(value, (list, dict)):
                        raise PipelineError("JSON 嵌套字段请先展开，不能直接导入。")
                    values.append(None if pd.isna(value) or value in nulls else value)
                rows.append(tuple(values))
                if len(rows) >= batch_size:
                    insert_batch(cursor, sql, rows)
                    count += len(rows)
                    rows = []
            if rows:
                insert_batch(cursor, sql, rows)
                count += len(rows)
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        after = cursor.fetchone()[0]
        drain(cursor)
        if after != count:
            raise PipelineError("导入行数与数据库行数不一致。")
        conn.commit()
        return count
    finally:
        cursor.close()


def scalar_equal(actual, expected):
    if actual is None or expected is None:
        return actual is expected
    try:
        return Decimal(str(actual)) == Decimal(str(expected))
    except Exception:
        return actual == expected


def check_result(cursor, item):
    if not cursor.description:
        raise PipelineError("校验查询没有返回结果集。")
    first = cursor.fetchone()
    if item["expect"] == "zero_rows":
        passed = first is None
    else:
        second = cursor.fetchone() if first is not None else None
        passed = (first is not None and len(first) == 1 and second is None
                  and scalar_equal(first[0], item["value"]))
    drain(cursor)
    return passed


def acquire_lock(conn, database):
    # Connection-scoped lock releases on close, including failed runs.
    key = "ai_sql_pipeline:" + hashlib.sha256(database.encode("utf-8")).hexdigest()[:40]
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT GET_LOCK(%s, 0)", (key,))
        row = cursor.fetchone()
        drain(cursor)
        if row is None or row[0] != 1:
            raise PipelineError("同一数据库已有流水线在运行，或无法取得执行锁；本次停止。")
    finally:
        cursor.close()


def execute_plan(root, config, plan, conn, run_dir, report):
    events = report["events"]
    for relative, digest in plan["hashes"].items():
        if file_hash(root / relative) != digest:
            raise PipelineError("执行前文件发生变化，请重新预览。")
    # DDL auto-commits in MySQL: never claim a failed run can be fully rolled back.
    run_layers(conn, plan["layers"]["01_ods"], root, events)
    for path, item in plan["imports"]:
        event = {"step": "import", "file": str(path.relative_to(root)), "table": item["table"]}
        events.append(event)
        event["rows"] = import_data(conn, path, item, config.get("sql_pipeline", {}).get("batch_size", 1000))
        event["status"] = "passed"
    for layer in ("02_dwd", "03_ads"):
        run_layers(conn, plan["layers"][layer], root, events)
    for path, query, item in plan["checks"]:
        event = {"step": "check", "file": str(path.relative_to(root)), "name": item["name"]}
        events.append(event)
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            passed = check_result(cursor, item)
            event["status"] = "passed" if passed else "failed"
            if not passed:
                raise PipelineError(f"校验未通过：{item['name']}；本次不生成交付表。")
        finally:
            cursor.close()
    conn.commit()
    # A single consistent read snapshot for all exports (InnoDB source tables).
    cursor = conn.cursor()
    try:
        cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        conn.commit()
        cursor.execute("START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY")
    finally:
        cursor.close()
    temporary = run_dir / "tables.partial"
    temporary.mkdir()
    for path, query, item in plan["exports"]:
        event = {"step": "export", "name": item["name"], "file": str(path.relative_to(root))}
        events.append(event)
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            if not cursor.description:
                raise PipelineError("导出查询没有返回结果集。")
            total = 0
            with (temporary / f"{item['name']}.csv").open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow([col[0] for col in cursor.description])
                while rows := cursor.fetchmany(1000):
                    writer.writerows(rows)
                    total += len(rows)
            drain(cursor)
            event.update(status="passed", rows=total)
        finally:
            cursor.close()
    conn.commit()
    # Published only after model capture and temporary-environment cleanup succeed.


def connect(config):
    import mysql.connector
    db = config["database"]
    env = db.get("password_env", "MYSQL_PASSWORD")
    if env not in os.environ:
        raise PipelineError(f"请在本机设置密码环境变量 {env}，不要把密码写入配置或聊天。")
    kwargs = {"host": db.get("host", "127.0.0.1"), "port": db.get("port", 3306),
              "user": db["user"], "password": os.environ[env], "charset": "utf8mb4",
              "autocommit": False, "connection_timeout": 10, "get_warnings": False,
              "raise_on_warnings": False, "allow_local_infile": False}
    if db.get("ssl_ca"):
        kwargs.update(ssl_ca=db["ssl_ca"], ssl_verify_cert=True, ssl_verify_identity=True)
    if not db.get("create_if_missing", False):
        kwargs["database"] = db["name"]
    conn = mysql.connector.connect(**kwargs)
    try:
        if db.get("create_if_missing", False):
            cursor = conn.cursor()
            try:
                # Check first so IF NOT EXISTS notices do not become failures.
                cursor.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s", (db["name"],))
                exists = cursor.fetchone()
                drain(cursor)
                if not exists:
                    cursor.execute(f"CREATE DATABASE {identifier(db['name'])} CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
                    conn.commit()
            finally:
                cursor.close()
            conn.database = db["name"]
        # Do not permit silent truncation of imported values.
        cursor = conn.cursor()
        try:
            cursor.execute("SET SESSION sql_mode = CONCAT_WS(',', @@sql_mode, 'STRICT_ALL_TABLES')")
            drain(cursor)
        finally:
            cursor.close()
        return conn
    except Exception:
        conn.close()
        raise


def run(root, config_path, execute=False, connection_factory=None, runtime_factory=TemporaryMySQL):
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    run_dir = root / "outputs" / "runs" / run_id
    run_dir.mkdir(parents=True)
    report = {"run_id": run_id, "mode": "execute" if execute else "preview", "status": "failed", "events": []}
    conn = None
    runtime = None
    try:
        config, plan = load_plan(root, config_path)
        batch_size = config.get("sql_pipeline", {}).get("batch_size", 1000)
        if not isinstance(batch_size, int) or batch_size < 1:
            raise PipelineError("batch_size 必须为正整数。")
        report["input_sha256"] = plan["hashes"]
        db = config["database"]
        target = {"mode": db["mode"], "database": db["name"]}
        if db["mode"] == "existing":
            target.update(host=db.get("host", "127.0.0.1"), port=db.get("port", 3306), user=db["user"],
                          create_if_missing=db.get("create_if_missing", False))
        else:
            target["runtime"] = config.get("temporary_mysql", {}).get("backend", "auto")
        report["plan"] = {"target": target,
                          "sql_files": [str(p.relative_to(root)) for scripts in plan["layers"].values() for p, parts in scripts if parts],
                          "imports": [i["table"] for _, i in plan["imports"]],
                          "checks": [i["name"] for _, _, i in plan["checks"]],
                          "exports": [i["name"] for _, _, i in plan["exports"]]}
        if execute:
            snapshot_sources(root, plan, run_dir)
            if connection_factory is not None:
                conn = connection_factory(config)
            elif db["mode"] == "temporary":
                runtime = runtime_factory(db["name"], config.get("temporary_mysql", {}))
                report["runtime"] = runtime.state
                conn = runtime.start()
            else:
                conn = connect(config)
            report["engine"] = engine_info(conn)
            acquire_lock(conn, db["name"])
            execute_plan(root, config, plan, conn, run_dir, report)
            report["model"] = save_model(conn, db["name"], plan, run_dir)
            conn.close()
            conn = None
            if runtime:
                runtime.close()
            (run_dir / "tables.partial").rename(run_dir / "tables")
            artifact_manifest(run_dir)
            report["status"] = "passed"
        else:
            report["status"] = "preview_only"
        return 0, run_dir, report
    except Exception as exc:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        # Driver messages may contain passwords, SQL literals or raw customer data.
        error = str(exc) if isinstance(exc, (PipelineError, RuntimeUnavailable)) else type(exc).__name__
        report["error"] = {"message": error, "errno": getattr(exc, "errno", None), "sqlstate": getattr(exc, "sqlstate", None)}
        if report["events"] and "status" not in report["events"][-1]:
            report["events"][-1]["status"] = "failed"
        return 1, run_dir, report
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        if runtime and runtime.state.get("cleanup") != "completed":
            try:
                runtime.close()
            except Exception:
                report["status"] = "failed"
                report["cleanup_error"] = "临时环境清理失败，请检查本次 runtime 记录。"
        # If manifest saving failed, never leave a formally published tables folder.
        if report["status"] == "failed" and (run_dir / "tables").exists():
            (run_dir / "tables").rename(run_dir / "tables.partial")
        (run_dir / "run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="预览/执行项目 MySQL SQL 流水线；不调用大模型，不需要 OpenAI Key。")
    parser.add_argument("--config", default="config.example.yaml")
    parser.add_argument("--project-dir", default=str(ROOT), help="项目根目录，默认本仓库")
    parser.add_argument("--execute", action="store_true", help="实际连接数据库并执行已审核的 SQL")
    args = parser.parse_args()
    root = Path(args.project_dir).resolve()
    path = (root / args.config).resolve()
    if not path.is_relative_to(root):
        parser.error("配置文件必须位于项目目录。")
    code, directory, report = run(root, path, args.execute)
    print(json.dumps({"status": report["status"], "plan": report.get("plan"), "report": str(directory / "run.json"), "error": report.get("error")}, ensure_ascii=False, indent=2))
    sys.exit(code)


if __name__ == "__main__":
    main()
