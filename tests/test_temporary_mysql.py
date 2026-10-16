import csv
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from scripts.run_sql_pipeline import ROOT, load_plan, run
from scripts.temporary_mysql import RuntimeUnavailable, TemporaryMySQL


class LifecycleTests(unittest.TestCase):
    def test_missing_runtime_cleans_start_failure_without_fallback(self):
        instance = TemporaryMySQL("analysis_run", {"backend": "docker"})
        with patch("scripts.temporary_mysql.shutil.which", return_value=None):
            with self.assertRaises(RuntimeUnavailable):
                instance.start()
        self.assertEqual(instance.state["cleanup"], "completed")
        self.assertIsNone(instance.connection)

    def test_temporary_preview_needs_no_user_or_password(self):
        root = ROOT / "examples/sql_pipeline_demo"
        config, plan = load_plan(root, root / "config.yaml")
        self.assertEqual(config["database"]["mode"], "temporary")
        self.assertNotIn("user", config["database"])
        self.assertEqual(len(plan["exports"]), 2)

    def test_docker_command_hides_password_and_removes_only_owned_resources(self):
        runtime = TemporaryMySQL("analysis_run", {"backend": "docker"})
        calls = []
        def fake_command(args, **kwargs):
            calls.append((args, kwargs))
            if args[1] == "inspect":
                return json.dumps([{"Image": "sha256:test", "NetworkSettings": {"Ports": {"3306/tcp": [{"HostIp": "127.0.0.1", "HostPort": "33333"}]}}}])
            if args[1] == "ps":
                return runtime.container
            return "ok"
        with patch("scripts.temporary_mysql.shutil.which", return_value="/usr/bin/docker"), patch("scripts.temporary_mysql.command", side_effect=fake_command):
            kwargs = runtime._docker()
            name = runtime.container
            self.assertEqual(kwargs, {"host": "127.0.0.1", "port": 33333})
            run_args, options = next(c for c in calls if c[0][1] == "run")
            self.assertNotIn(runtime.root_password, " ".join(run_args))
            self.assertEqual(options["env"]["MYSQL_ROOT_PASSWORD"], runtime.root_password)
            runtime.close()
        self.assertIn((["docker", "rm", "--force", "--volumes", name], {"timeout": 30}), calls)
        self.assertFalse(any("prune" in args for args, _ in calls))
        self.assertEqual(runtime.state["cleanup"], "completed")

    def test_docker_cleanup_failure_is_visible(self):
        runtime = TemporaryMySQL("analysis_run")
        runtime.container = "ai-sql-owned-test"
        def fake_command(args, **kwargs):
            if args[1] == "ps":
                return runtime.container
            raise RuntimeUnavailable("test failure")
        with patch("scripts.temporary_mysql.command", side_effect=fake_command):
            with self.assertRaises(RuntimeUnavailable):
                runtime.close()
        self.assertEqual(runtime.state["cleanup"], "failed")
        self.assertEqual(runtime.container, "ai-sql-owned-test")

    def test_initialization_exception_still_cleans_resources(self):
        runtime = TemporaryMySQL("analysis_run", {"backend": "native", "mysqld_path": "/missing"})
        with self.assertRaises(RuntimeUnavailable):
            runtime.start()
        self.assertEqual(runtime.state["cleanup"], "completed")


@unittest.skipUnless(os.environ.get("MYSQLD_PATH"), "requires a real MySQL 8.0 binary via MYSQLD_PATH")
class RealMySQLTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "project"
        shutil.copytree(ROOT / "examples/sql_pipeline_demo", self.root, ignore=shutil.ignore_patterns("outputs"))
        self.config_path = self.root / "config.yaml"
        self.config = yaml.safe_load(self.config_path.read_text())
        self.config["temporary_mysql"]["backend"] = "native"
        self.config["temporary_mysql"]["transport"] = os.environ.get("MYSQL_NATIVE_TRANSPORT", "unix")
        self.config_path.write_text(yaml.safe_dump(self.config, allow_unicode=True))
        self.instances = []

    def factory(self, *args):
        runtime = TemporaryMySQL(*args)
        self.instances.append(runtime)
        return runtime

    def assert_cleaned(self):
        self.assertTrue(self.instances)
        for runtime in self.instances:
            self.assertEqual(runtime.state["cleanup"], "completed")
            self.assertIsNone(runtime.directory)
            self.assertIsNone(runtime.process)
            self.assertIsNone(runtime.connection)

    def test_real_success_exports_model_source_and_cleans_database(self):
        code, directory, report = run(self.root, self.config_path, True, runtime_factory=self.factory)
        self.assertEqual(code, 0, report)
        self.assertTrue(report["engine"]["version"].startswith("8.0."))
        with (directory / "tables/类别汇总.csv").open(encoding="utf-8-sig") as f:
            data = list(csv.reader(f))
        self.assertEqual(data[1:], [["A", "2", "30.50"], ["B", "1", "30.00"]])
        with (directory / "tables/清洗明细.csv").open(encoding="utf-8-sig") as f:
            self.assertEqual(list(csv.DictReader(f))[0]["记录编号"], "001")
        self.assertEqual(report["model"], {"tables": 4, "fields": 12, "declared_foreign_keys": 1})
        schema = (directory / "model/schema.sql").read_text()
        self.assertIn("FOREIGN KEY", schema)
        fields = json.loads((directory / "model/model.json").read_text())["fields"]
        origin = next(c for c in fields if c["table_name"] == "原始_记录" and c["field_name"] == "记录编号")
        self.assertEqual(origin["source_field"], "record_id")
        self.assertEqual(origin["source_file"], "data/raw/records.csv")
        self.assertIn("CREATE TABLE", (directory / "source/sql/01_ods/01_create.sql").read_text())
        self.assertTrue((directory / "manifest.json").is_file())
        content = (directory / "run.json").read_text()
        self.assertNotIn(self.instances[0].password, content)
        self.assertNotIn(self.instances[0].root_password, content)
        self.assert_cleaned()

    def test_real_qa_failure_keeps_source_and_cleans_without_exports(self):
        self.config["sql_pipeline"]["checks"][1]["value"] = 999
        self.config_path.write_text(yaml.safe_dump(self.config, allow_unicode=True))
        code, directory, report = run(self.root, self.config_path, True, runtime_factory=self.factory)
        self.assertEqual(code, 1, report)
        self.assertFalse((directory / "tables").exists())
        self.assertTrue((directory / "source/sql/02_dwd/01_clean.sql").is_file())
        self.assertEqual(report["events"][-1]["status"], "failed")
        self.assert_cleaned()

    def test_real_sql_error_cleans_and_records_statement(self):
        path = self.root / "sql/02_dwd/01_clean.sql"
        path.write_text(path.read_text() + "\nSELECT missing_field FROM `原始_记录`;\n")
        code, directory, report = run(self.root, self.config_path, True, runtime_factory=self.factory)
        self.assertEqual(code, 1, report)
        self.assertEqual(report["error"]["errno"], 1054)
        self.assertEqual(report["events"][-1]["file"], "sql/02_dwd/01_clean.sql")
        self.assertFalse((directory / "tables").exists())
        self.assert_cleaned()


if __name__ == "__main__":
    unittest.main()
