"""Inject benchmark data into the report page template -> results/report.html"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from report import load  # noqa: E402

label = "ornith"
summary = json.loads((ROOT / "results/summary.json").read_text())[label]
tasks = [r for r in csv.DictReader(open(ROOT / "results/per_task.csv")) if r["model"] == label]
_, reqs, ev = load(label)
loadtest = [{k: v for k, v in r.items() if k != "raw"} for r in json.loads((ROOT / "results" / label / "loadtest.json").read_text())]
manifest = {m["id"]: m for m in json.loads((ROOT / "tasks/manifest.json").read_text())}

data = dict(
    summary=summary,
    tasks=[dict(id=t["task"], difficulty=t["difficulty"], passed=int(t["passed"]), tests=int(t["tests"]),
                wall=float(t["wall_s"]), requests=int(t["requests"]), out=int(t["completion_tokens"]),
                prompt=int(t["prompt_tokens"]), ttft=float(t["ttft_median_s"] or 0), rate=float(t["decode_tok_s_median"] or 0),
                starter=manifest[t["task"]]["starter_passed"]) for t in tasks],
    reqs=[dict(t=round(r["t_req"] / 60, 3), ttft=round(r["ttft"], 3), rate=round(r["rate"], 1) if r["rate"] else None,
               load=r["inflight"], task=r["tag"], out=r["completion"]) for r in reqs if r["ok"] and r["ttft"] is not None],
    inflight=[[round(t / 60, 3), d] for t, d in ev],
    loadtest=loadtest,
)
tpl = (ROOT / "harness/report_template.html").read_text(encoding="utf-8")
out = ROOT / "results/report.html"
out.write_text(tpl.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":"))), encoding="utf-8")
print(out, out.stat().st_size, "bytes")

ptpl = (ROOT / "harness/poster_template.html").read_text(encoding="utf-8")
pout = ROOT / "results/poster.html"
pout.write_text(ptpl.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":"))), encoding="utf-8")
print(pout)
