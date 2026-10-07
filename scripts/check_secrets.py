"""Scan versionable files without network verification or printing secret values."""

import json
import os
import subprocess
from pathlib import Path

from detect_secrets.core.secrets_collection import SecretsCollection
from detect_secrets.settings import transient_settings

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ".secrets.baseline"


def main():
    os.chdir(ROOT)
    baseline = json.loads(Path(BASELINE).read_text(encoding="utf-8"))
    known = {
        (filename, item["type"], item["hashed_secret"])
        for filename, findings in baseline["results"].items()
        for item in findings
        if item.get("is_secret") is False and item.get("review_reason")
    }
    paths = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        text=True,
        encoding="utf-8",
    ).split("\0")
    files = sorted({path for path in paths if path != BASELINE and Path(path).is_file()})
    collection = SecretsCollection()
    with transient_settings(baseline):
        for filename in files:
            collection.scan_file(filename)
    findings = collection.json()
    unknown = []
    for filename, items in findings.items():
        for item in items:
            if (filename.replace("\\", "/"), item["type"], item["hashed_secret"]) not in known:
                unknown.append(
                    {"file": filename, "line": item["line_number"], "type": item["type"]}
                )
    report = {"files_scanned": len(files), "unreviewed": unknown}
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 1 if unknown else 0


if __name__ == "__main__":
    raise SystemExit(main())
