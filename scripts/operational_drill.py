"""Isolated synthetic PostgreSQL restore/crash and real HTTPS drill; never uses DATABASE_URL."""

import argparse
import hashlib
import json
import multiprocessing
import os
import socket
import ssl
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import httpx
import psycopg
from cryptography import x509
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "nomi_drill_source"
RESTORED = "nomi_drill_restored"


class DrillFailure(RuntimeError):
    """Only labels authored in this script, safe for the report."""


def require(condition, label):
    if not condition:
        raise DrillFailure(label)


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def run(command, *, env=None, data=None):
    result = subprocess.run(
        [str(item) for item in command],
        cwd=ROOT,
        env=env,
        input=data,
        capture_output=True,
        timeout=120,
    )
    # Never echo arguments, stderr or bodies: they may contain credentials or financial data.
    require(result.returncode == 0, f"Command failed: {Path(command[0]).name}")
    return result.stdout


def certificate(directory):
    """Private test CA is trusted only by this drill, never installed in the OS/browser."""
    now = datetime.now(UTC)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Nomi drill CA")])
    ca = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=2))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), False)
        .add_extension(
            x509.KeyUsage(False, False, False, False, False, True, True, None, None), True
        )
        .sign(ca_key, hashes.SHA256())
    )
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")]))
        .issuer_name(ca_name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), True)
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), False
        )
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), False)
        .add_extension(
            x509.KeyUsage(True, False, True, False, False, False, False, None, None), True
        )
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), False)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), False)
        .sign(ca_key, hashes.SHA256())
    )
    (directory / "ca.pem").write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    (directory / "server.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    private_file(
        directory / "server.key",
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ),
    )


def private_file(path, data):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def serve_api(directory, port, environment):
    os.environ.update(environment)
    os.chdir(ROOT)
    with (directory / "api.log").open("a", encoding="utf-8") as log:
        sys.stdout = sys.stderr = log
        import uvicorn

        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=port,
            access_log=False,
            proxy_headers=False,
            ssl_keyfile=str(directory / "server.key"),
            ssl_certfile=str(directory / "server.pem"),
        )


def snapshot(connection):
    tables = connection.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
    ).fetchall()
    result = {}
    for (table,) in tables:
        rows = connection.execute(
            sql.SQL("SELECT row_to_json(t)::text FROM {} t ORDER BY row_to_json(t)::text").format(
                sql.Identifier(table)
            )
        ).fetchall()
        digest = hashlib.sha256()
        for (row,) in rows:
            digest.update(row.encode() + b"\n")
        result[table] = {"count": len(rows), "sha256": digest.hexdigest()}
    return result


def invariants(connection):
    checks = {
        "balance_matches_history": """
            SELECT count(*) FROM commitments c WHERE c.balance_minor !=
            c.original_amount_minor - COALESCE((SELECT sum(CASE WHEN t.type='payment'
                THEN t.amount_minor ELSE -t.amount_minor END)
                FROM transactions t WHERE t.commitment_id=c.id),0)""",
        "balance_status": """SELECT count(*) FROM commitments WHERE
            balance_minor < 0 OR balance_minor > original_amount_minor OR version < 1 OR
            (lifecycle_status='paid' AND balance_minor != 0) OR
            (lifecycle_status='open' AND balance_minor <= 0)""",
        "reversal_relationship": """SELECT count(*) FROM transactions r
            LEFT JOIN transactions p ON r.reversal_of_transaction_id=p.id
            WHERE r.type='reversal' AND (p.id IS NULL OR p.type!='payment' OR
            p.amount_minor!=r.amount_minor OR p.currency_code!=r.currency_code OR
            p.commitment_id!=r.commitment_id)""",
        "single_reversal": """SELECT count(*) FROM (SELECT reversal_of_transaction_id
            FROM transactions WHERE reversal_of_transaction_id IS NOT NULL
            GROUP BY reversal_of_transaction_id HAVING count(*)>1) duplicates""",
        "owner_membership": """SELECT count(*) FROM users u WHERE NOT EXISTS
            (SELECT 1 FROM memberships m WHERE m.user_id=u.id AND m.role='owner')""",
        "constraints_validated": """SELECT count(*) FROM pg_constraint
            WHERE connamespace='public'::regnamespace AND NOT convalidated""",
        "currency": """SELECT count(*) FROM commitments c JOIN workspaces w
            ON c.workspace_id=w.id WHERE c.currency_code!=w.currency_code OR EXISTS
            (SELECT 1 FROM transactions t WHERE t.commitment_id=c.id
            AND t.currency_code!=c.currency_code)""",
    }
    for label, query in checks.items():
        require(connection.execute(query).fetchone()[0] == 0, label)
    return list(checks)


class Drill:
    def __init__(self, pg_bin):
        self.pg_bin = pg_bin
        self.directory = ROOT / ".local" / "operational-drills" / uuid4().hex
        self.directory.mkdir(parents=True)
        self.data = self.directory / "postgres"
        self.pg_port, self.api_port = free_port(), free_port()
        while self.api_port == self.pg_port:
            self.api_port = free_port()
        self.origin = f"https://localhost:{self.api_port}"
        self.api = None
        self.pg_started = False
        self.mail_key = Fernet.generate_key()
        self.report = {"started_at": datetime.now(UTC).isoformat(), "scope": "isolated-local"}

    def pg(self, command, *args, **kwargs):
        suffix = ".exe" if os.name == "nt" else ""
        executable = self.pg_bin / (command + suffix)
        if command == "pg_ctl":
            # Windows postgres can inherit a pipe handle from pg_ctl and keep communicate()
            # waiting after pg_ctl exits. Use regular files and detached stdin instead.
            with (self.directory / "pg_ctl.log").open("ab") as log:
                result = subprocess.run(
                    [str(executable), *map(str, args)],
                    cwd=ROOT,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=log,
                    timeout=120,
                )
            require(result.returncode == 0, "Command failed: pg_ctl")
            return b""
        return run([executable, *args], **kwargs)

    def connect(self, database=SOURCE, **kwargs):
        require(database in (SOURCE, RESTORED, "postgres"), "Unexpected database")
        return psycopg.connect(
            host="127.0.0.1", port=self.pg_port, user="nomi_drill", dbname=database, **kwargs
        )

    def env(self, database):
        return {
            **os.environ,
            "DATABASE_URL": f"postgresql+psycopg://nomi_drill@127.0.0.1:{self.pg_port}/{database}",
            "ENVIRONMENT": "staging",
            "COOKIE_SECURE": "true",
            "APP_ORIGIN": self.origin,
            "ACCOUNT_MAIL_KEY": self.mail_key.decode(),
            # No worker is started. Pending mail must survive backup; no external SMTP is used.
            "MAIL_BACKEND": "smtp",
            "SMTP_HOST": "127.0.0.1",
            "SMTP_PORT": "1",
        }

    def start_pg(self):
        # Mark ownership before startup so cleanup also covers a partially successful start.
        self.pg_started = True
        self.pg(
            "pg_ctl",
            "-D",
            self.data,
            "-l",
            self.directory / "postgres.log",
            "-o",
            f"-p {self.pg_port} -h 127.0.0.1 -c log_error_verbosity=terse "
            "-c log_min_error_statement=panic",
            "-w",
            "start",
        )

    def stop_pg(self, mode="fast"):
        if self.pg_started:
            if (self.data / "postmaster.pid").exists():
                self.pg("pg_ctl", "-D", self.data, "-m", mode, "-w", "stop")
            self.pg_started = False

    def start_api(self, database):
        self.stop_api()
        self.api = multiprocessing.get_context("spawn").Process(
            target=serve_api,
            args=(self.directory, self.api_port, self.env(database)),
        )
        self.api.start()
        with self.client() as client:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                require(self.api.is_alive(), "HTTPS API exited during startup")
                try:
                    if client.get("/health/ready").status_code == 200:
                        return
                except httpx.TransportError as error:
                    if "CERTIFICATE_VERIFY_FAILED" in str(error):
                        raise DrillFailure("HTTPS certificate validation failed") from None
                time.sleep(0.2)
        raise DrillFailure("HTTPS API readiness timeout")

    def stop_api(self):
        if self.api is not None:
            self.api.terminate()
            self.api.join(timeout=10)
            if self.api.is_alive():
                self.api.kill()
                self.api.join(timeout=10)
            self.api = None

    def client(self):
        return httpx.Client(
            base_url=self.origin,
            verify=ssl.create_default_context(cafile=str(self.directory / "ca.pem")),
            headers={"Origin": self.origin},
            trust_env=False,
            timeout=10,
        )

    def token(self, database, purpose, email):
        table = {"verify": "email_verification_tokens", "reset": "password_reset_tokens"}[purpose]
        with self.connect(database) as connection:
            encrypted = connection.execute(
                sql.SQL(
                    "SELECT t.delivery_secret FROM {} t JOIN users u ON t.user_id=u.id "
                    "WHERE u.email=%s AND t.used_at IS NULL ORDER BY t.created_at DESC LIMIT 1"
                ).format(sql.Identifier(table)),
                (email,),
            ).fetchone()[0]
        return Fernet(self.mail_key).decrypt(encrypted.encode()).decode()

    def request(self, client, method, path, status=200, **kwargs):
        response = client.request(method, "/api/v1" + path, **kwargs)
        require(response.status_code == status, f"HTTP {method} {path}: expected {status}")
        return response.json() if response.content else None

    def seed(self):
        self.password = "Drill-" + uuid4().hex
        self.email = "restore-drill@example.com"
        self.start_api(SOURCE)
        with self.client() as client:
            profile = self.request(
                client,
                "POST",
                "/auth/register",
                201,
                json={
                    "display_name": "Synthetic restore drill",
                    "email": self.email,
                    "password": self.password,
                },
            )
            require(not profile["can_operate"], "Verification gate missing")
            self.request(client, "GET", "/dashboard/summary", 403)
            self.request(
                client,
                "POST",
                "/auth/email/verify",
                json={
                    "token": self.token(SOURCE, "verify", self.email),
                },
            )
            cookies = {cookie.name: cookie for cookie in client.cookies.jar}
            require(cookies["nomi_session"].secure, "Session cookie not Secure")
            require(cookies["nomi_session"].has_nonstandard_attr("HttpOnly"), "Missing HttpOnly")
            require(cookies["nomi_session"].get_nonstandard_attr("SameSite") == "lax", "SameSite")
            require(cookies["nomi_csrf"].secure, "CSRF cookie not Secure")
            self.request(client, "POST", "/contacts", 403, json={"name": "Rejected CSRF"})
            client.headers["X-CSRF-Token"] = client.cookies["nomi_csrf"]
            self.request(
                client,
                "POST",
                "/contacts",
                403,
                headers={"Origin": "https://invalid.example"},
                json={"name": "Rejected"},
            )
            contact = self.request(client, "POST", "/contacts", 201, json={"name": "Synthetic"})
            self.contact_id = contact["id"]
            commitment = self.request(
                client,
                "POST",
                "/commitments",
                201,
                headers={"Idempotency-Key": str(uuid4())},
                json={
                    "contact_id": contact["id"],
                    "direction": "receivable",
                    "original_amount_minor": 1000000,
                    "currency_code": "MXN",
                },
            )
            self.commitment_id = commitment["id"]
            self.payment_path = f"/commitments/{self.commitment_id}/transactions"
            self.payment_key = str(uuid4())
            self.payment_body = {
                "amount_minor": 250000,
                "expected_version": 1,
                "occurred_at": datetime.now(UTC).isoformat(),
            }
            self.payment = self.request(
                client,
                "POST",
                self.payment_path,
                201,
                headers={"Idempotency-Key": self.payment_key},
                json=self.payment_body,
            )
            self.request(
                client,
                "POST",
                f"/transactions/{self.payment['transaction']['id']}/reverse",
                201,
                headers={"Idempotency-Key": str(uuid4())},
                json={"expected_version": 2},
            )
            self.request(
                client,
                "POST",
                self.payment_path,
                201,
                headers={"Idempotency-Key": str(uuid4())},
                json={**self.payment_body, "expected_version": 3},
            )
            self.history = self.request(client, "GET", self.payment_path)
            self.dashboard = self.request(client, "GET", "/dashboard/summary")
            require(self.dashboard["receivable_balance_minor"] == "750000", "Seed balance")
            self.session_cookies = dict(client.cookies)
            plain = client.build_request(
                "GET", self.origin.replace("https://", "http://") + "/api/v1/me"
            )
            require("cookie" not in plain.headers, "Secure cookies attached to plain HTTP")
            self.request(client, "POST", "/auth/password/forgot", 202, json={"email": self.email})
        # The certificate must fail without the drill CA and for a mismatched hostname.
        for url, context in [
            (self.origin, ssl.create_default_context()),
            (
                self.origin.replace("localhost", "127.0.0.1"),
                ssl.create_default_context(cafile=str(self.directory / "ca.pem")),
            ),
        ]:
            try:
                httpx.get(url + "/health/ready", verify=context, trust_env=False, timeout=5)
            except httpx.ConnectError as error:
                require("CERTIFICATE_VERIFY_FAILED" in str(error), "Unexpected TLS failure")
            else:
                raise DrillFailure("Invalid TLS certificate was accepted")
        self.report["https"] = [
            "trusted_test_CA",
            "untrusted_CA_rejected",
            "hostname_mismatch_rejected",
            "Secure_HttpOnly_SameSite",
            "Secure_cookies_not_attached_to_HTTP",
            "CSRF_and_origin",
            "verification_gate",
        ]
        self.stop_api()

    def backup_restore(self):
        started = time.monotonic()
        pg_args = ["-h", "127.0.0.1", "-p", str(self.pg_port), "-U", "nomi_drill"]
        with self.connect() as connection:
            connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            snapshot_id = connection.execute("SELECT pg_export_snapshot()").fetchone()[0]
            before = snapshot(connection)
            self.report["invariants"] = invariants(connection)
            archive = self.pg("pg_dump", *pg_args, "-Fc", "--snapshot", snapshot_id, SOURCE)
        backup_key = Fernet.generate_key()
        encrypted = Fernet(backup_key).encrypt(archive)
        private_file(self.directory / "backup.key", backup_key)
        private_file(self.directory / "source.dump.fernet", encrypted)
        private_file(self.directory / "account-mail.key", self.mail_key)
        del archive
        # Read the saved backup/key back from disk, including negative integrity checks.
        encrypted = (self.directory / "source.dump.fernet").read_bytes()
        cipher = Fernet((self.directory / "backup.key").read_bytes())
        for decoder, payload in [
            (Fernet(Fernet.generate_key()), encrypted),
            (cipher, encrypted[: len(encrypted) // 2]),
        ]:
            try:
                decoder.decrypt(payload)
            except InvalidToken:
                pass
            else:
                raise DrillFailure("Damaged backup or wrong key was accepted")
        self.report["backup_seconds"] = round(time.monotonic() - started, 3)
        restore_started = time.monotonic()
        self.pg("createdb", *pg_args, RESTORED)
        self.pg(
            "pg_restore",
            *pg_args,
            "--dbname",
            RESTORED,
            "--exit-on-error",
            "--single-transaction",
            "--no-owner",
            "--no-acl",
            data=cipher.decrypt(encrypted),
        )
        run([sys.executable, "-m", "alembic", "upgrade", "head"], env=self.env(RESTORED))
        run([sys.executable, "-m", "alembic", "check"], env=self.env(RESTORED))
        with self.connect(RESTORED) as connection:
            require(snapshot(connection) == before, "Restored tables differ from backup snapshot")
            invariants(connection)
        self.report["restore_and_schema_check_seconds"] = round(
            time.monotonic() - restore_started, 3
        )
        self.report["tables"] = before
        self.report["backup_integrity"] = [
            "wrong_key_rejected",
            "truncation_rejected",
            "all_rows_equal",
        ]

    def crash_recovery(self):
        # Only our fresh synthetic cluster is stopped. The user's normal instance stays running.
        started = time.monotonic()
        connection = self.connect(RESTORED)
        try:
            connection.execute(
                "UPDATE contacts SET name=%s WHERE id=%s", ("Uncommitted change", self.contact_id)
            )
            self.stop_pg("immediate")
        finally:
            connection.close()
        self.start_pg()
        with self.connect(RESTORED) as connection:
            require(snapshot(connection) == self.report["tables"], "Crash recovery changed data")
            invariants(connection)
        self.report["crash_recovery_seconds"] = round(time.monotonic() - started, 3)
        self.report["crash_recovery"] = "committed_rows_preserved_uncommitted_change_rolled_back"

    def restored_smoke(self):
        self.mail_key = (self.directory / "account-mail.key").read_bytes()
        self.start_api(RESTORED)
        with self.client() as client:
            client.cookies.update(self.session_cookies)
            client.headers["X-CSRF-Token"] = self.session_cookies["nomi_csrf"]
            require(
                self.request(client, "GET", "/dashboard/summary") == self.dashboard, "Dashboard"
            )
            require(self.request(client, "GET", self.payment_path) == self.history, "History")
            replay = self.request(
                client,
                "POST",
                self.payment_path,
                201,
                headers={"Idempotency-Key": self.payment_key},
                json=self.payment_body,
            )
            require(replay == self.payment, "Idempotent replay changed after restore")
            require(
                self.request(client, "GET", self.payment_path) == self.history, "Duplicated payment"
            )
            reset_token = self.token(RESTORED, "reset", self.email)
            new_password = "Restored-" + uuid4().hex
            self.request(
                client,
                "POST",
                "/auth/password/reset",
                json={"token": reset_token, "password": new_password},
            )
            client.cookies.clear()
            client.cookies.update(self.session_cookies)
            self.request(client, "GET", "/me", 401)
            client.cookies.clear()
            self.request(
                client,
                "POST",
                "/auth/login",
                401,
                json={"email": self.email, "password": self.password},
            )
            self.request(
                client, "POST", "/auth/login", json={"email": self.email, "password": new_password}
            )
            self.request(
                client,
                "POST",
                "/auth/password/reset",
                400,
                json={"token": reset_token, "password": new_password},
            )
            require(
                self.request(client, "GET", "/dashboard/summary") == self.dashboard, "Reset balance"
            )
            require(self.request(client, "GET", self.payment_path) == self.history, "Reset history")
        self.report["restored_smoke"] = [
            "dashboard",
            "history",
            "idempotent_replay",
            "session",
            "encrypted_reset_token",
            "revocation",
            "new_password",
        ]

    def execute(self):
        started = time.monotonic()
        try:
            print("Creating isolated synthetic cluster and HTTPS certificate", flush=True)
            certificate(self.directory)
            self.pg(
                "initdb",
                "-D",
                self.data,
                "-U",
                "nomi_drill",
                "--auth=trust",
                "--encoding=UTF8",
                "--locale=C",
            )
            self.start_pg()
            self.pg(
                "createdb", "-h", "127.0.0.1", "-p", str(self.pg_port), "-U", "nomi_drill", SOURCE
            )
            run([sys.executable, "-m", "alembic", "upgrade", "head"], env=self.env(SOURCE))
            print("Checking HTTPS, secure session and financial flow", flush=True)
            self.seed()
            print("Encrypting backup, restoring and comparing every table", flush=True)
            self.backup_restore()
            print("Testing isolated PostgreSQL crash recovery", flush=True)
            self.crash_recovery()
            print("Checking restored API, replay and account recovery", flush=True)
            self.restored_smoke()
            self.report["status"] = "passed"
        except Exception as error:
            self.report["status"] = "failed"
            self.report["error_type"] = type(error).__name__
            if isinstance(error, DrillFailure):
                self.report["failed_check"] = str(error)
            raise
        finally:
            cleanup_errors = []
            for stop in (self.stop_api, self.stop_pg):
                try:
                    stop()
                except Exception:
                    cleanup_errors.append(stop.__name__)
            if cleanup_errors:
                self.report["status"] = "failed"
                self.report["cleanup_errors"] = cleanup_errors
            self.report["elapsed_seconds"] = round(time.monotonic() - started, 3)
            (self.directory / "report.json").write_text(
                json.dumps(self.report, indent=2), encoding="utf-8"
            )
            print(f"Report: {self.directory / 'report.json'}", flush=True)
            if cleanup_errors:
                raise DrillFailure("Could not stop all owned drill processes; inspect report")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pg-bin", type=Path, default=Path("C:/Program Files/PostgreSQL/18/bin"))
    args = parser.parse_args()
    require(not sys.flags.optimize, "Run without -O")
    try:
        Drill(args.pg_bin).execute()
    except Exception as error:
        # Keep a generic failure summary; logs and report stay in the private local directory.
        print(
            f"Drill failed ({type(error).__name__}). "
            + (str(error) if isinstance(error, DrillFailure) else "Inspect the local report/logs."),
            file=sys.stderr,
        )
        sys.exit(1)
