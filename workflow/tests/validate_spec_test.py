#!/usr/bin/env python3
"""validate_spec_test.py — validate_spec.py on scratch projects whose root path contains spaces (no example project).

Cases: the per-project template spec (templates/shotspec.template.json) and the neutral fixture
(fixtures/spec-neutral.json, which sets every optional worldfilm block) are valid; mutated copies of the fixture are
INVALID and name each defect; a fixture whose footage mask dir was never written fails on that alone.
The projects are built in a fresh temporary directory; a copy of every generated spec and validator output is kept
in <out>/spec-cases/ for inspection.
usage: validate_spec_test.py --python <interpreter> --out <dir>     exit 0 when every expectation holds
"""
import argparse, copy, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WF = os.path.dirname(HERE)
VALIDATE = os.path.join(WF, "scripts", "validate_spec.py")


def project(root, name, spec, masks=True):
    d = os.path.join(root, name)
    os.makedirs(d)
    if masks:
        for s in spec.get("shots", []):
            fl = s.get("footage_layer")
            if fl:
                os.makedirs(os.path.join(d, fl["mask_dir"]), exist_ok=True)
    p = os.path.join(d, "shotspec.json")
    json.dump(spec, open(p, "w"), indent=1)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    keep = os.path.join(os.path.abspath(a.out), "spec-cases")
    os.makedirs(keep, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="worldfilm spec cases ") as tmp:
        run_cases(a, os.path.join(tmp, "projects root"), keep)


def run_cases(a, root, keep):
    results = []

    def check(name, spec_path, want_rc, reasons=()):
        r = subprocess.run([a.python, VALIDATE, spec_path], capture_output=True, text=True)
        out = r.stdout + r.stderr
        slug = os.path.basename(os.path.dirname(spec_path)).replace(" ", "-")
        with open(os.path.join(keep, slug + ".json"), "w") as f, open(spec_path) as src:
            f.write(src.read())
        with open(os.path.join(keep, slug + ".out.txt"), "w") as f:
            f.write("exit %d\n%s" % (r.returncode, out))
        missing = [x for x in reasons if x not in out]
        ok = r.returncode == want_rc and not missing
        results.append((ok, name, "exit %d (wanted %d)%s; %s" % (r.returncode, want_rc, " missing %s" % missing if missing else "", out.strip()[-400:])))

    tpl = json.load(open(os.path.join(WF, "templates", "shotspec.template.json")))
    check("the template spec is valid in a new project at a path with spaces", project(root, "new project", tpl), 0)
    good = json.load(open(os.path.join(HERE, "fixtures", "spec-neutral.json")))
    check("the neutral fixture (every optional block set) is valid", project(root, "neutral film", good), 0, ["valid:"])
    check("the neutral fixture without its footage mask dir is INVALID", project(root, "no masks", good, masks=False), 1, ["footage_layer.mask_dir"])

    bad = copy.deepcopy(good)
    bad["project"]["gates"]["hyperframes_cmd"] = "/opt/some path/hyperframes"
    bad["project"]["camera"]["rest_drift"]["vertical_units"] = 0
    bad["project"]["camera"]["rest_drift"]["boosts"][0]["to_s"] = 9.0
    bad["audio"]["silence"] = [[5.8, 5.5]]
    bad["audio"]["cues"][1]["event"] = "tile-1"
    s1, s2 = bad["shots"]
    s1["world_anchors"][0]["text_id"] = "L-missing"
    s1["camera"]["poses"].reverse()
    s2["camera"]["framing_target"]["hold_from_s"] = 3.5
    check("a mutated fixture is INVALID and names all eight defects", project(root, "broken film", bad), 1, [
        "hyperframes_cmd", "vertical_units 0", "boosts: window", "audio.silence", "duplicate event bindings",
        "refers to text_id 'L-missing'", "camera poses are not sorted", "hold_from_s is before its last key"])

    nodial = copy.deepcopy(good)
    del nodial["project"]["camera"]["dial"]
    check("camera poses without a project dial are INVALID", project(root, "no dial", nodial), 1, ["dial"])

    bad_n = sum(1 for ok, _, _ in results if not ok)
    for ok, name, detail in results:
        print(("ok   " if ok else "FAIL ") + name + ("" if ok else "\n       " + detail))
    print("validate_spec_test: %d/%d expectations hold" % (len(results) - bad_n, len(results)))
    sys.exit(1 if bad_n else 0)


if __name__ == "__main__":
    main()
