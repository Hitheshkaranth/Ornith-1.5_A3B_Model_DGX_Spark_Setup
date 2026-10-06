"""Materialise tasks/ from the taskdefs and validate each hidden test suite against its reference solution."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import taskdefs_a, taskdefs_b, taskdefs_c, taskdefs_d  # noqa: E402

TASKS = taskdefs_a.TASKS + taskdefs_b.TASKS + taskdefs_c.TASKS + taskdefs_d.TASKS


def write_files(base, files):
    for rel, content in files.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8", newline="\n")


def score(ws, test_file):
    r = subprocess.run([sys.executable, str(HERE / "run_hidden.py"), str(ws), str(test_file)],
                       capture_output=True, text=True, timeout=600)
    return json.loads(r.stdout.strip().splitlines()[-1])


def main():
    out_dir = ROOT / "tasks"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    manifest, ok = [], True
    for t in TASKS:
        d = out_dir / t["id"]
        (d / "starter").mkdir(parents=True, exist_ok=True)
        write_files(d / "starter", t["starter"])
        write_files(d / "ref", t["ref"])
        (d / "prompt.md").write_text(t["prompt"], encoding="utf-8", newline="\n")
        (d / "test_hidden.py").write_text(t["tests"], encoding="utf-8", newline="\n")
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp) / "ws"
            shutil.copytree(d / "starter", ws)
            base = score(ws, d / "test_hidden.py")
            shutil.copytree(d / "ref", ws, dirs_exist_ok=True)
            refres = score(ws, d / "test_hidden.py")
        good = refres["tests"] > 0 and refres["passed"] == refres["tests"]
        ok &= good
        print("%-28s ref %2d/%2d  starter %2d  %s %s" % (t["id"], refres["passed"], refres["tests"], base["passed"],
                                                       "OK" if good else "FAIL", refres.get("failed") or refres.get("import_error") or ""))
        manifest.append(dict(id=t["id"], difficulty=t["difficulty"], tests=refres["tests"], starter_passed=base["passed"]))
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
