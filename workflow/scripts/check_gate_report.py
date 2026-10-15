#!/usr/bin/env python3
"""check_gate_report.py — the pass/fail reader for a run_gates.py gate-report.json (worldfilm stage 7 and 9).

run_gates.py exits 0 when nothing FAILED; it does not fail on a SKIPPED gate, and its frozen_time gate passes at
exactly the limit. A command path containing spaces can prevent a gate from running; the resulting SKIP must
not count as success. Small differences in sampling or motion blur can move a render across a threshold.
One frozen-time sample represents 0.1 seconds, normalised by the report's actual analysis-window length.

This reader exits non-zero when:
  - the summary verdict is FAIL;
  - any gate is SKIP and is not named in --allow-skip (a skipped gate is NOT a passed gate; allow a skip only
    with the reason written in GAUNTLET.jsonl, e.g. --allow-skip handoff,swatch when the spec declares no carry
    object and no swatch points);
  - frozen_time is within --frozen-margin-samples samples of its limit (default 2);
  - --require names a gate that is absent from the report.
It prints one line per gate that matters and the reason, so build.sh logs show WHY a stage did not pass.

usage: check_gate_report.py gates/draft-7/gate-report.json [--allow-skip handoff,swatch] [--frozen-margin-samples 2]
                            [--require contrast,facts,read_time] [--quiet]
exit 0 pass, 1 not passed, 2 usage
"""
import argparse
import json
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report")
    ap.add_argument("--allow-skip", default="", help="comma list of gates that may be SKIP (write the reason in the ledger)")
    ap.add_argument("--frozen-margin-samples", type=int, default=2, help="frozen_time must sit this many 10 fps samples under its limit (default 2)")
    ap.add_argument("--require", default="", help="comma list of gates that must be present in the report")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    try:
        rep = json.load(open(a.report))
    except Exception as e:
        print("check_gate_report: cannot read %s: %s" % (a.report, e))
        sys.exit(2)
    gates = {g.get("gate") or g.get("name"): g for g in rep.get("gates", [])}
    allow = {s.strip() for s in a.allow_skip.split(",") if s.strip()}
    problems = []
    say = (lambda *x: None) if a.quiet else print

    summary = rep.get("summary", {})
    if summary.get("verdict") == "FAIL":
        problems.append("verdict FAIL: %s" % ", ".join(summary.get("failed_gates", [])))
    for name in [s.strip() for s in a.require.split(",") if s.strip()]:
        if name not in gates:
            problems.append("required gate %s is missing from the report" % name)
    for name, g in gates.items():
        st = g.get("status")
        if st == "SKIP":
            if name in allow:
                say("  skip allowed  %-14s %s" % (name, g.get("detail", "")))
            else:
                problems.append("%s SKIPPED (not passed): %s" % (name, g.get("detail", "")))
        elif st == "FAIL":
            say("  FAIL          %-14s %s" % (name, (g.get("detail") or "")[:160]))
    fz = gates.get("frozen_time")
    if fz and fz.get("status") in ("PASS", "WARN", "FAIL"):
        m, t = fz.get("measured", {}), fz.get("threshold", {})
        limit = t.get("frozen_max_s_per_30s")
        per30 = m.get("frozen_s_per_30s")
        win = m.get("analysed_window_s")
        total = m.get("frozen_total_s")
        if limit is not None and total is not None and (not isinstance(win, (int, float)) or win <= 0):
            problems.append("frozen_time report lacks a positive analysed_window_s; margin cannot be verified")
        elif limit is not None and total is not None:
            n = int(round(total * 10))                                   # frozen samples (10 fps)
            limit_n = int((limit * win / 30.0) * 10 + 1e-6)              # samples allowed in this analysed window
            sample = 0.1 * 30.0 / max(0.1, win)                          # one sample, normalised per 30 s
            if n > limit_n - a.frozen_margin_samples:
                problems.append("frozen_time %d frozen samples (%.2f s/30s) vs %d allowed: fewer than %d samples of margin "
                                "(one sample = %.3f s/30s; a blur master or a Docker render reads +-1 sample from a draft)"
                                % (n, per30 if per30 is not None else n * sample, limit_n, a.frozen_margin_samples, sample))
            else:
                say("  margin ok     frozen_time    %d of %d samples (%.2f s/30s, limit %.2f), %d samples of margin"
                    % (n, limit_n, per30 if per30 is not None else n * sample, limit, limit_n - n))
    if problems:
        print("check_gate_report: NOT PASSED (%s)" % a.report)
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("check_gate_report: PASSED (%s): %d PASS, %d WARN, %d allowed skip" % (
        a.report, summary.get("pass", 0), summary.get("warn", 0), sum(1 for g in gates.values() if g.get("status") == "SKIP")))


if __name__ == "__main__":
    main()
