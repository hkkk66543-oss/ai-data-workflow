"""Disposable MySQL 8.0 lifecycle. Never uses or deletes an existing database."""
from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import socket as sockets
import subprocess
import tempfile
import time
import uuid
from pathlib import Path


class RuntimeUnavailable(Exception):
    pass


def command(args, timeout=60, env=None):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeUnavailable(f"临时 MySQL 命令未能完成：{type(exc).__name__}") from None
    if result.returncode:
        # Captured output can contain runtime secrets or user SQL: do not echo it.
        raise RuntimeUnavailable("临时 MySQL 命令失败；检查运行依赖、镜像网络或 mysqld 动态库。")
    return result.stdout.strip()


class TemporaryMySQL:
    def __init__(self, database, settings=None):
        if not re.fullmatch(r"\w{1,64}", database, re.UNICODE):
            raise RuntimeUnavailable("临时数据库名称无效。")
        self.database = database
        self.settings = settings or {}
        self.password = secrets.token_urlsafe(32)
        self.root_password = secrets.token_urlsafe(32)
        self.bootstrap_password = ""
        self.container = None
        self.process = None
        self.directory = None
        self.log = None
        self.connection = None
        self.state = {"mode": "temporary", "cleanup": "not_started"}

    def start(self):
        import mysql.connector
        backend = self.settings.get("backend", "auto")
        native_path = self.settings.get("mysqld_path") or os.environ.get("MYSQLD_PATH")
        if backend == "auto":
            backend = "native" if native_path else "docker"
        self.state["backend"] = backend
        try:
            if backend == "docker":
                kwargs = self._docker()
            elif backend == "native":
                kwargs = self._native(native_path)
            else:
                raise RuntimeUnavailable("temporary_mysql.backend 只支持 auto/docker/native。")
            deadline = time.monotonic() + self.settings.get("startup_timeout", 120)
            admin = None
            while time.monotonic() < deadline:
                if self.process and self.process.poll() is not None:
                    raise RuntimeUnavailable("临时 mysqld 提前退出，请检查二进制运行依赖。")
                try:
                    admin = mysql.connector.connect(**kwargs, user="root", password=self.bootstrap_password,
                                                    connection_timeout=2, autocommit=True)
                    break
                except mysql.connector.Error:
                    time.sleep(0.5)
            if admin is None:
                raise RuntimeUnavailable("临时 MySQL 启动超时，未执行业务 SQL。")
            try:
                cursor = admin.cursor()
                try:
                    cursor.execute("SELECT VERSION(), @@version_comment")
                    version, comment = cursor.fetchone()
                    if not version.startswith("8.0.") or "mariadb" in (version + comment).lower():
                        raise RuntimeUnavailable("临时环境不是 MySQL 8.0，拒绝替代验证。")
                    self.state.update(version=version, version_comment=comment)
                    cursor.execute(f"CREATE DATABASE `{self.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
                    host = "%" if backend == "docker" else "localhost"
                    cursor.execute("CREATE USER 'pipeline'@%s IDENTIFIED BY %s", (host, self.password))
                    cursor.execute(f"GRANT ALL PRIVILEGES ON `{self.database}`.* TO 'pipeline'@%s", (host,))
                    if backend == "native":
                        cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY %s", (self.root_password,))
                finally:
                    cursor.close()
            finally:
                admin.close()
            self.connection = mysql.connector.connect(**kwargs, user="pipeline", password=self.password,
                                                       database=self.database, charset="utf8mb4", autocommit=False,
                                                       get_warnings=False, raise_on_warnings=False,
                                                       allow_local_infile=False, connection_timeout=10)
            cursor = self.connection.cursor()
            try:
                cursor.execute("SET SESSION sql_mode = CONCAT_WS(',', @@sql_mode, 'STRICT_ALL_TABLES')")
            finally:
                cursor.close()
            return self.connection
        except BaseException:
            # Also clean up initialization and readiness failures, not only successful starts.
            self.close()
            raise

    def _docker(self):
        if not shutil.which("docker"):
            raise RuntimeUnavailable("执行环境缺少 Docker。请在具备 Docker 的执行环境运行，或提供 MYSQLD_PATH 使用原生临时进程；无需本地 MySQL 账号。")
        command(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=15)
        image = self.settings.get("image", "mysql:8.0.46")
        # Run only an explicitly versioned 8.0 image; actual server version is checked too.
        if not re.fullmatch(r"(?:[\w.:-]+/)*mysql(?::8\.0(?:\.\d+)?(?:-[\w.-]+)?)(?:@sha256:[a-f0-9]{64})?", image):
            raise RuntimeUnavailable("镜像必须是显式标注 8.0 的 mysql 镜像。")
        self.container = "ai-sql-" + uuid.uuid4().hex
        self.state["container_name"] = self.container
        self.bootstrap_password = self.root_password
        env = dict(os.environ, MYSQL_ROOT_PASSWORD=self.root_password, MYSQL_ROOT_HOST="%")
        # No secret in argv or project files; only a disposable container environment.
        # Anonymous data volume is removed with this exact container by rm -v.
        command(["docker", "run", "--detach", "--name", self.container,
                 "--label", "ai-data-workflow.temporary=true", "--publish", "127.0.0.1::3306",
                 "--env", "MYSQL_ROOT_PASSWORD", "--env", "MYSQL_ROOT_HOST", image,
                 "--character-set-server=utf8mb4", "--collation-server=utf8mb4_0900_ai_ci",
                 "--local-infile=0", "--skip-log-bin"], timeout=self.settings.get("startup_timeout", 120), env=env)
        info = json.loads(command(["docker", "inspect", self.container]))[0]
        self.state["container_name"] = self.container
        self.state["image_id"] = info["Image"]
        self.state["image"] = image
        port = info["NetworkSettings"]["Ports"]["3306/tcp"][0]
        if port["HostIp"] != "127.0.0.1":
            raise RuntimeUnavailable("临时 MySQL 端口未限制为本机回环地址。")
        return {"host": "127.0.0.1", "port": int(port["HostPort"])}

    def _native(self, native_path):
        if os.name != "posix" or not native_path:
            raise RuntimeUnavailable("原生临时模式要求 Linux/Unix 和现成 MySQL 8.0 mysqld 路径；Windows 可在 Docker 执行环境运行。")
        binary = Path(native_path).resolve()
        version = command([str(binary), "--no-defaults", "--version"], timeout=15)
        if not re.search(r"\bVer 8\.0\.\d+", version) or "mariadb" in version.lower():
            raise RuntimeUnavailable("mysqld 二进制必须是 MySQL 8.0。")
        self.directory = Path(tempfile.mkdtemp(prefix="ai-sql-"))
        self.directory.chmod(0o700)
        self.state["temporary_directory"] = str(self.directory)
        data = self.directory / "data"
        socket = self.directory / "mysql.sock"
        common = [str(binary), "--no-defaults", f"--basedir={binary.parent.parent}", f"--datadir={data}"]
        if os.geteuid() == 0:
            common.append("--user=root")
        self.log = (self.directory / "server.log").open("w")
        try:
            result = subprocess.run(common + ["--initialize-insecure"], stdout=self.log, stderr=self.log,
                                    timeout=self.settings.get("startup_timeout", 120))
        except subprocess.TimeoutExpired:
            raise RuntimeUnavailable("MySQL 临时数据目录初始化超时。") from None
        if result.returncode:
            raise RuntimeUnavailable("MySQL 临时数据目录初始化失败。")
        transport = self.settings.get("transport", "unix")
        if transport == "unix":
            network_args = ["--skip-networking", f"--socket={socket}"]
            kwargs = {"unix_socket": str(socket)}
        elif transport == "tcp":
            # Environments without AF_UNIX can bind only loopback TCP. Initialize
            # the root password through a private init file BEFORE accepting clients.
            with sockets.socket() as reservation:
                reservation.bind(("127.0.0.1", 0))
                port = reservation.getsockname()[1]
            init = self.directory / "init.sql"
            init.write_text("ALTER USER 'root'@'localhost' IDENTIFIED BY '" + self.root_password + "';\n")
            init.chmod(0o600)
            self.bootstrap_password = self.root_password
            network_args = ["--bind-address=127.0.0.1", f"--port={port}", "--socket=", f"--init-file={init}"]
            kwargs = {"host": "127.0.0.1", "port": port}
        else:
            raise RuntimeUnavailable("native transport 只支持 unix/tcp。")
        self.process = subprocess.Popen(common + network_args + ["--mysqlx=0",
                                                  f"--pid-file={self.directory / 'mysql.pid'}", "--skip-log-bin",
                                                  "--local-infile=0", "--innodb-buffer-pool-size=64M",
                                                  "--character-set-server=utf8mb4", "--collation-server=utf8mb4_0900_ai_ci"],
                                        stdout=self.log, stderr=self.log)
        self.state["process_id"] = self.process.pid
        self.state["binary_version"] = version
        self.state["transport"] = transport
        return kwargs

    def close(self):
        failures = []
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None
        if self.container:
            try:
                # Never prune or remove resources not created by this instance.
                # Docker run might have timed out while pulling; remove an existing
                # owned name, and treat an absent container as already cleaned.
                listing = command(["docker", "ps", "--all", "--filter", f"name=^/{self.container}$", "--format", "{{.Names}}"], timeout=15)
                if listing == self.container:
                    command(["docker", "rm", "--force", "--volumes", self.container], timeout=30)
                self.container = None
            except Exception:
                failures.append("container")
        if self.process:
            try:
                if self.process.poll() is None:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait(timeout=10)
                self.process = None
            except Exception:
                failures.append("process")
        if self.log:
            self.log.close()
            self.log = None
        if self.directory and not self.process:
            try:
                shutil.rmtree(self.directory)
                self.directory = None
            except Exception:
                failures.append("directory")
        self.state["cleanup"] = "failed" if failures else "completed"
        if failures:
            raise RuntimeUnavailable("临时环境清理未完成：" + ",".join(failures) + "；请检查运行报告，勿清理其他项目资源。")
