"""Executor contract tests using a fake driver, not a real MySQL server."""
import csv
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import yaml

from scripts.run_sql_pipeline import (
    PipelineError, check_result, frames, identifier, import_data, load_plan,
    run, scalar_equal, statements,
)


class Cursor:
    def __init__(self, conn):
        self.conn = conn
        self.description = None
        self.rows = []
        self.closed = False

    def execute(self, sql, params=None):
        self.conn.executed.append(sql)
        self.rows = []
        self.description = None
        if self.conn.fail_on and self.conn.fail_on in sql:
            raise RuntimeError("sensitive raw value/password should never appear in logs")
        if sql.startswith("SELECT GET_LOCK"):
            self.description = [("lock",)]
            self.rows = [(self.conn.lock_result,)]
        elif sql == "SHOW COUNT(*) WARNINGS":
            self.description = [("warnings",)]
            self.rows = [(self.conn.warning_count,)]
        elif sql.startswith("SELECT COUNT(*)"):
            self.description = [("count",)]
            self.rows = [(self.conn.imported,)]
        elif sql.startswith("SELECT"):
            self.description, rows = self.conn.answers.get(sql, ([("value",)], []))
            self.rows = list(rows)

    def executemany(self, sql, rows):
        self.conn.executed.append(sql)
        self.conn.inserted.extend(rows)
        self.conn.imported += len(rows)

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None

    def fetchmany(self, n=1):
        result, self.rows = self.rows[:n], self.rows[n:]
        return result

    def nextset(self):
        return None

    def close(self):
        self.closed = True


class Connection:
    def __init__(self):
        self.executed = []
        self.answers = {}
        self.imported = 0
        self.lock_result = 1
        self.warning_count = 0
        self.inserted = []
        self.rollbacks = 0
        self.fail_on = None
        self.closed = False

    def cursor(self):
        return Cursor(self)

    def commit(self):
        pass

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in ("sql/01_ods", "sql/02_dwd", "sql/03_ads", "sql/04_checks", "data/raw"):
            (self.root / directory).mkdir(parents=True)
        self.write("sql/01_ods/01.sql", "CREATE TABLE 原始 (id VARCHAR(20));")
        self.write("sql/02_dwd/01.sql", "CREATE TABLE 清洗 AS SELECT * FROM 原始;")
        self.write("sql/03_ads/01.sql", "CREATE TABLE 应用 AS SELECT * FROM 清洗;")
        self.write("sql/03_ads/export.sql", "SELECT id FROM 应用;")
        self.write("sql/04_checks/unique.sql", "SELECT id FROM 清洗 GROUP BY id HAVING COUNT(*) > 1;")
        self.write("data/raw/input.csv", "source_id,value\n00123,NA\n00456,\n")
        self.config = {"database": {"name": "test_db", "user": "tester", "mode": "existing"}, "sql_pipeline": {
            "batch_size": 1,
            "imports": [{"file": "data/raw/input.csv", "table": "原始", "columns": {"source_id": "id"}}],
            "checks": [{"name": "唯一性", "sql_file": "sql/04_checks/unique.sql", "expect": "zero_rows"}],
            "exports": [{"name": "应用", "sql_file": "sql/03_ads/export.sql"}],
        }}
        self.path = self.root / "config.local.yaml"
        self.save_config()
        engine = patch("scripts.run_sql_pipeline.engine_info", return_value={"version": "8.0.fake"})
        model = patch("scripts.run_sql_pipeline.save_model", return_value={"tables": 3, "fields": 3})
        engine.start()
        model.start()
        self.addCleanup(engine.stop)
        self.addCleanup(model.stop)

    def write(self, path, content):
        (self.root / path).write_text(content, encoding="utf-8")

    def save_config(self):
        self.path.write_text(yaml.safe_dump(self.config, allow_unicode=True), encoding="utf-8")

    def test_preview_never_connects_and_excludes_export_from_ads_execution(self):
        code, directory, report = run(self.root, self.path, connection_factory=lambda _: self.fail("preview connected"))
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "preview_only")
        self.assertNotIn("sql/03_ads/export.sql", report["plan"]["sql_files"])
        self.assertFalse((directory / "tables").exists())

    def test_success_executes_in_order_imports_once_and_streams_exports(self):
        conn = Connection()
        conn.answers["SELECT id FROM 应用"] = ([("id",)], [(str(n),) for n in range(2100)])
        code, directory, report = run(self.root, self.path, True, lambda _: conn)
        self.assertEqual(code, 0, report)
        self.assertEqual(conn.inserted, [("00123",), ("00456",)])
        self.assertLess(conn.executed.index("CREATE TABLE 原始 (id VARCHAR(20))"), next(i for i, s in enumerate(conn.executed) if s.startswith("INSERT")))
        self.assertLess(conn.executed.index("CREATE TABLE 应用 AS SELECT * FROM 清洗"), conn.executed.index("SELECT id FROM 应用"))
        self.assertEqual(conn.executed.count("SELECT id FROM 应用"), 1)
        with (directory / "tables/应用.csv").open(encoding="utf-8-sig", newline="") as f:
            self.assertEqual(len(list(csv.reader(f))), 2101)
        self.assertTrue(conn.closed)
        self.assertEqual(json.loads((directory / "run.json").read_text())["status"], "passed")

    def test_failed_check_blocks_all_exports(self):
        conn = Connection()
        conn.answers["SELECT id FROM 清洗 GROUP BY id HAVING COUNT(*) > 1"] = ([("id",)], [("duplicate",)])
        code, directory, report = run(self.root, self.path, True, lambda _: conn)
        self.assertEqual(code, 1)
        self.assertEqual(report["events"][-1]["status"], "failed")
        self.assertNotIn("SELECT id FROM 应用", conn.executed)
        self.assertFalse((directory / "tables").exists())
        self.assertGreater(conn.rollbacks, 0)

    def test_driver_failure_stops_downstream_and_redacts_details(self):
        conn = Connection()
        conn.fail_on = "CREATE TABLE 清洗"
        code, directory, report = run(self.root, self.path, True, lambda _: conn)
        self.assertEqual(code, 1)
        self.assertNotIn("CREATE TABLE 应用 AS SELECT * FROM 清洗", conn.executed)
        self.assertNotIn("sensitive", (directory / "run.json").read_text())
        self.assertEqual(report["events"][-1]["file"], "sql/02_dwd/01.sql")

    def test_second_export_failure_never_publishes_partial_tables(self):
        self.write("sql/03_ads/export2.sql", "SELECT other FROM 应用;")
        self.config["sql_pipeline"]["exports"].append({"name": "其他", "sql_file": "sql/03_ads/export2.sql"})
        self.save_config()
        conn = Connection()
        conn.fail_on = "SELECT other"
        code, directory, _ = run(self.root, self.path, True, lambda _: conn)
        self.assertEqual(code, 1)
        self.assertTrue((directory / "tables.partial/应用.csv").exists())
        self.assertFalse((directory / "tables").exists())

    def test_busy_database_lock_blocks_sql(self):
        conn = Connection()
        conn.lock_result = 0
        code, directory, report = run(self.root, self.path, True, lambda _: conn)
        self.assertEqual(code, 1)
        self.assertEqual(report["events"], [])
        self.assertFalse(any(s.startswith("CREATE TABLE") for s in conn.executed))
        self.assertTrue(conn.closed)

    def test_model_capture_failure_does_not_publish_tables(self):
        conn = Connection()
        with patch("scripts.run_sql_pipeline.save_model", side_effect=OSError("disk error")):
            code, directory, report = run(self.root, self.path, True, lambda _: conn)
        self.assertEqual(code, 1)
        self.assertFalse((directory / "tables").exists())
        self.assertTrue((directory / "tables.partial").exists())
        self.assertTrue((directory / "source/sql/01_ods/01.sql").exists())

    def test_temporary_cleanup_failure_does_not_publish_tables(self):
        self.config["database"]["mode"] = "temporary"
        self.save_config()
        class Runtime:
            state = {"cleanup": "not_started"}
            def start(inner):
                return Connection()
            def close(inner):
                inner.state["cleanup"] = "failed"
                raise PipelineError("cleanup failed")
        code, directory, report = run(self.root, self.path, True, runtime_factory=lambda *args: Runtime())
        self.assertEqual(code, 1)
        self.assertEqual(report["runtime"]["cleanup"], "failed")
        self.assertFalse((directory / "tables").exists())

    def test_import_warning_stops_pipeline_and_rolls_back(self):
        conn = Connection()
        conn.warning_count = 1
        code, directory, report = run(self.root, self.path, True, lambda _: conn)
        self.assertEqual(code, 1)
        self.assertGreater(conn.rollbacks, 0)
        self.assertFalse(any(s.startswith("CREATE TABLE 清洗") for s in conn.executed))
        self.assertFalse((directory / "tables").exists())

    def test_nonempty_import_refuses_duplicate_rows(self):
        conn = Connection()
        conn.imported = 2
        with self.assertRaises(PipelineError):
            import_data(conn, self.root / "data/raw/input.csv", self.config["sql_pipeline"]["imports"][0], 1)
        self.assertEqual(conn.inserted, [])

    def test_comment_only_layers_and_missing_checks_fail_preflight(self):
        self.write("sql/01_ods/01.sql", "-- template only\n")
        with self.assertRaises(PipelineError):
            load_plan(self.root, self.path)
        self.write("sql/01_ods/01.sql", "CREATE TABLE test(id INT);")
        self.config["sql_pipeline"]["checks"] = []
        self.save_config()
        with self.assertRaises(PipelineError):
            load_plan(self.root, self.path)

    def test_sql_parser_preserves_semicolons_and_quoted_comment_markers(self):
        p = self.root / "sql/01_ods/01.sql"
        p.write_text("-- header\nINSERT INTO test VALUES ('a;b', '--text');\n/* c */ SELECT 1;", encoding="utf-8")
        parts = statements(p)
        self.assertEqual(len(parts), 2)
        self.assertIn("'a;b'", parts[0])
        self.assertIn("'--text'", parts[0])
        for text in ("USE other;", "DROP DATABASE other;", "DELIMITER $$\nSELECT 1$$", "/*!50000 DROP TABLE t */;"):
            p.write_text(text)
            with self.assertRaises(PipelineError):
                statements(p)

    def test_paths_names_and_check_queries_are_validated(self):
        for name in ("a.b", "a`b", "../file", ""):
            with self.assertRaises(PipelineError):
                identifier(name)
        self.config["sql_pipeline"]["imports"][0]["file"] = "../outside.csv"
        self.save_config()
        with self.assertRaises(PipelineError):
            load_plan(self.root, self.path)
        self.config["sql_pipeline"]["imports"] = []
        self.save_config()
        self.write("sql/04_checks/unique.sql", "SELECT 1; SELECT 2;")
        with self.assertRaises(PipelineError):
            load_plan(self.root, self.path)

    def test_scalar_checks_require_exact_one_by_one_shape(self):
        for rows, expected in (([(0,)], True), ([(1,)], False), ([], False), ([(0,), (0,)], False), ([(0, 0)], False)):
            cur = Cursor(Connection())
            cur.description = [("value",)]
            cur.rows = rows.copy()
            self.assertEqual(check_result(cur, {"expect": "scalar_equals", "value": 0}), expected)
        self.assertTrue(scalar_equal(Decimal("0.00"), 0))
        self.assertFalse(scalar_equal(None, 0))

    def test_csv_preserves_leading_zero_and_na_literal(self):
        frame = next(frames(self.root / "data/raw/input.csv", {}, 100))
        self.assertEqual(frame.loc[0, "source_id"], "00123")
        self.assertEqual(frame.loc[0, "value"], "NA")
        self.assertEqual(frame.loc[1, "value"], "")

    def test_xlsx_and_json_import_use_explicit_mapping_and_nulls(self):
        path = self.root / "data/raw/input.xlsx"
        pd.DataFrame({"source_id": ["00123", "00456"], "value": ["NA", ""]}).to_excel(path, index=False)
        frame = next(frames(path, {}, 10))
        self.assertEqual(frame.loc[0, "source_id"], "00123")
        self.assertEqual(frame.loc[0, "value"], "NA")
        path = self.root / "data/raw/input.json"
        path.write_text(json.dumps([{"id": "00123", "value": None}]))
        conn = Connection()
        count = import_data(conn, path, {"table": "原始", "columns": {"id": "记录编号", "value": "指标值"}}, 10)
        self.assertEqual(count, 1)
        self.assertEqual(conn.inserted, [("00123", None)])
        path.write_text('{"id": "wrong JSON shape"}')
        with self.assertRaises(PipelineError):
            next(frames(path, {}, 10))

    def test_input_mutation_after_plan_is_detected_before_sql(self):
        from scripts.run_sql_pipeline import execute_plan
        config, plan = load_plan(self.root, self.path)
        self.write("data/raw/input.csv", "changed\n1\n")
        conn = Connection()
        with self.assertRaises(PipelineError):
            execute_plan(self.root, config, plan, conn, self.root, {"events": []})
        self.assertEqual(conn.executed, [])


if __name__ == "__main__":
    unittest.main()
