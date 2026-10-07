"""Reproducible local load sample on a NEW synthetic cluster, never the user's database."""

import argparse
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from operational_drill import Drill, certificate, invariants, require, run


def percentiles(values):
    ordered = sorted(values)
    return {
        "count": len(values),
        "p50_ms": round(ordered[math.ceil(len(values) * 0.50) - 1], 2),
        "p95_ms": round(ordered[math.ceil(len(values) * 0.95) - 1], 2),
        "max_ms": round(ordered[-1], 2),
    }


class LoadDrill(Drill):
    def fixtures(self):
        # Synthetic fixtures ONLY: no production connections, no arbitrary edits of user money.
        with self.connect() as db:
            self.user_id, self.workspace_id = db.execute(
                "SELECT user_id,workspace_id FROM memberships LIMIT 1"
            ).fetchone()
            db.execute(
                """INSERT INTO contacts (id,workspace_id,name,created_at,updated_at)
                SELECT gen_random_uuid(),%s,'Synthetic load '||n,now(),now()
                FROM generate_series(1,5000) n""",
                (self.workspace_id,),
            )
            db.execute("""INSERT INTO commitments
                (id,workspace_id,contact_id,direction,original_amount_minor,balance_minor,
                 currency_code,concept,lifecycle_status,version,created_at,updated_at)
                SELECT gen_random_uuid(),workspace_id,id,'receivable',10000,7500,'MXN',
                       'Synthetic load', 'open',2,now(),now() FROM contacts
                CROSS JOIN generate_series(1,2) n WHERE name LIKE 'Synthetic load %%'""")
            db.execute(
                """INSERT INTO transactions
                (id,commitment_id,type,amount_minor,currency_code,occurred_at,created_at,created_by)
                SELECT gen_random_uuid(),id,'payment',2500,'MXN',now(),now(),%s
                FROM commitments WHERE concept='Synthetic load'""",
                (self.user_id,),
            )
            self.ids = [
                str(row[0])
                for row in db.execute(
                    "SELECT id FROM commitments WHERE concept='Synthetic load' ORDER BY id LIMIT 100"
                )
            ]
            self.report["seed_counts"] = {
                table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                for table in ("contacts", "commitments", "transactions")
            }
            invariants(db)
        with self.connect(autocommit=True) as db:
            db.execute("ANALYZE")

    def workload(self):
        self.start_api("nomi_drill_source")
        csrf = self.session_cookies["nomi_csrf"]
        headers = {"X-CSRF-Token": csrf}

        # One persistent client per thread. Establish TLS once before timed requests.
        def reader(worker):
            samples = {"dashboard": [], "search": [], "history": []}
            with self.client() as client:
                client.cookies.update(self.session_cookies)
                self.request(client, "GET", "/me")
                for _ in range(15):
                    for kind, path in (
                        ("dashboard", "/dashboard/summary"),
                        ("search", "/commitments?search=Synthetic%20load%2042&limit=30"),
                        ("history", f"/commitments/{self.ids[worker]}/transactions?limit=30"),
                    ):
                        started = time.perf_counter()
                        response = self.request(client, "GET", path)
                        samples[kind].append((time.perf_counter() - started) * 1000)
                        if kind == "dashboard":
                            require(
                                response["receivable_balance_minor"] == "75750000", "Loaded summary"
                            )
            return samples

        started = time.monotonic()
        with ThreadPoolExecutor(max_workers=8) as pool:
            readers = list(pool.map(reader, range(8)))
        self.report["read_seconds"] = round(time.monotonic() - started, 3)
        self.report["reads"] = {
            kind: percentiles([v for group in readers for v in group[kind]]) for kind in readers[0]
        }

        def writer(batch):
            elapsed = []
            with self.client() as client:
                client.cookies.update(self.session_cookies)
                self.request(client, "GET", "/me")
                for identifier in batch:
                    started = time.perf_counter()
                    result = self.request(
                        client,
                        "POST",
                        f"/commitments/{identifier}/transactions",
                        201,
                        headers={**headers, "Idempotency-Key": str(uuid4())},
                        json={
                            "expected_version": 2,
                            "amount_minor": 100,
                            "occurred_at": datetime.now(UTC).isoformat(),
                        },
                    )
                    require(result["commitment"]["balance_minor"] == 7400, "Write balance")
                    elapsed.append((time.perf_counter() - started) * 1000)
            return elapsed

        with ThreadPoolExecutor(max_workers=8) as pool:
            writes = list(pool.map(writer, [self.ids[i::8] for i in range(8)]))
        self.report["writes"] = percentiles([v for group in writes for v in group])
        with self.client() as client:
            client.cookies.update(self.session_cookies)
            response = self.request(
                client, "POST", "/exports/workspace", 422, headers=headers, json={}
            )
            require(
                response["code"] == "EXPORT_LIMIT_EXCEEDED", "Large export must reject explicitly"
            )
        with self.connect() as db:
            self.report["invariants"] = invariants(db)
            total = db.execute(
                "SELECT sum(balance_minor) FROM commitments WHERE lifecycle_status='open'"
            ).fetchone()[0]
            require(total == 75740000, "Final balance after concurrent writes")
        # A local regression budget, not a public SLO or a prediction of hosting capacity.
        require(
            all(
                group["p95_ms"] < 3000
                for group in [*self.report["reads"].values(), self.report["writes"]]
            ),
            "Local p95 exceeded 3000ms; inspect and tune before declaring this run passed",
        )

    def execute(self):
        started = time.monotonic()
        try:
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
                "createdb",
                "-h",
                "127.0.0.1",
                "-p",
                str(self.pg_port),
                "-U",
                "nomi_drill",
                "nomi_drill_source",
            )
            run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                env=self.env("nomi_drill_source"),
            )
            print("Seeding isolated synthetic load data", flush=True)
            self.seed()
            self.fixtures()
            print(
                "Running 360 reads and 100 writes, eight concurrent clients, over HTTPS", flush=True
            )
            self.workload()
            self.report["status"] = "passed"
        except Exception as error:
            self.report["status"] = "failed"
            self.report["error_type"] = type(error).__name__
            raise
        finally:
            self.stop_api()
            self.stop_pg()
            self.report["elapsed_seconds"] = round(time.monotonic() - started, 3)
            (self.directory / "load-report.json").write_text(
                json.dumps(self.report, indent=2), encoding="utf-8"
            )
            print(f"Report: {self.directory / 'load-report.json'}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pg-bin", type=Path, default=Path("C:/Program Files/PostgreSQL/18/bin"))
    LoadDrill(parser.parse_args().pg_bin).execute()
