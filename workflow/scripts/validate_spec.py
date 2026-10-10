#!/usr/bin/env python3
"""validate_spec.py — validate a worldfilm spec against schema/worldfilm.schema.json, which extends shotspec-film's
schema/shotspec.schema.json by $ref (old ShotSpecs validate unchanged). Also checks the cross-references the schema
cannot: every shots[].world_anchors[].text_id exists in that shot's text[], every audio.cues[].event is unique,
footage_layer.mask_dir exists, camera poses are sorted in time, the dial is set when any shot has camera poses,
framing_target keys are in order and inside the shot, rest-drift boosts and silence windows lie inside the film,
the gate runner command is "npx hyperframes", and (warnings) variant compositions and the music-only stem exist.

usage: validate_spec.py shotspec.json [--schema schema/worldfilm.schema.json] [--shotspec-schema <path>]
exit 0 valid, 1 invalid, 2 usage / dependency error
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def find_shotspec_schema(explicit):
    cands = [explicit, os.environ.get("SHOTSPEC_HOME", "") and os.path.join(os.environ["SHOTSPEC_HOME"], "schema", "shotspec.schema.json"),
             os.path.join(HERE, "..", "..", "studio", "kits", "shotspec-film", "schema", "shotspec.schema.json"),
             os.path.expanduser("~/.codex/skills/shotspec-film/schema/shotspec.schema.json")]
    for c in cands:
        if c and os.path.exists(c):
            return os.path.abspath(c)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--schema", default=os.path.join(HERE, "..", "schema", "worldfilm.schema.json"))
    ap.add_argument("--shotspec-schema", default=None)
    a = ap.parse_args()
    try:
        import jsonschema
        from referencing import Registry, Resource
    except Exception as e:
        print("missing dependency: %s (uv pip install jsonschema into studio/.venv)" % e)
        sys.exit(2)
    base = find_shotspec_schema(a.shotspec_schema)
    if not base:
        print("shotspec.schema.json not found (install shotspec-film or pass --shotspec-schema)")
        sys.exit(2)
    wf = json.load(open(a.schema))
    ss = json.load(open(base))
    spec = json.load(open(a.spec))
    registry = Registry().with_resources([(ss["$id"], Resource.from_contents(ss)), (wf["$id"], Resource.from_contents(wf))])
    v = jsonschema.Draft202012Validator(wf, registry=registry)
    errors = ["schema: %s: %s" % ("/".join(str(p) for p in e.absolute_path) or "<root>", e.message) for e in sorted(v.iter_errors(spec), key=lambda e: list(e.absolute_path))]
    proj = spec.get("project", {})
    shots = spec.get("shots", [])
    has_cam = False
    for s in shots:
        texts = {t.get("id") for t in s.get("text", [])}
        for wa in s.get("world_anchors", []) or []:
            if wa.get("text_id") and wa["text_id"] not in texts:
                errors.append("%s: world_anchors %s refers to text_id %r not in this shot's text[]" % (s.get("id"), wa.get("id"), wa.get("text_id")))
        cam = s.get("camera") or {}
        poses = cam.get("poses") or []
        if poses:
            has_cam = True
            ts = [p["t"] for p in poses]
            if ts != sorted(ts):
                errors.append("%s: camera poses are not sorted in time" % s.get("id"))
            if ts and (ts[0] < s["t_in"] - 1e-6 or ts[-1] > s["t_out"] + 1e-6):
                errors.append("%s: camera poses outside [t_in, t_out]" % s.get("id"))
        fl = s.get("footage_layer")
        if fl and not os.path.isdir(os.path.join(os.path.dirname(os.path.abspath(a.spec)), fl.get("mask_dir", ""))):
            errors.append("%s: footage_layer.mask_dir %r does not exist" % (s.get("id"), fl.get("mask_dir")))
    if has_cam and "dial" not in (proj.get("camera") or {}):
        errors.append("project.camera.dial must be set when any shot carries camera poses")
    events = [c.get("event") for c in (spec.get("audio", {}).get("cues") or []) if c.get("event")]
    if len(events) != len(set(events)):
        errors.append("audio.cues: duplicate event bindings %s" % sorted({e for e in events if events.count(e) > 1}))
    warnings = []
    dur = float(proj.get("duration") or 0)
    spec_dir = os.path.dirname(os.path.abspath(a.spec))
    for s in shots:
        ft = (s.get("camera") or {}).get("framing_target")
        if ft:
            kt = [k[0] for k in ft.get("keys", [])]
            if kt != sorted(kt):
                errors.append("%s: framing_target keys are not sorted in time" % s.get("id"))
            if kt and (kt[0] < s["t_in"] - 1e-6 or kt[-1] > s["t_out"] + 1e-6):
                errors.append("%s: framing_target keys outside [t_in, t_out]" % s.get("id"))
            if kt and ft.get("hold_from_s") is not None and ft["hold_from_s"] < kt[-1] - 1e-6:
                errors.append("%s: framing_target.hold_from_s is before its last key" % s.get("id"))
            if len(kt) > 1 and max(b - a_ for a_, b in zip(kt, kt[1:])) > float(ft.get("key_step_s", 0.1)) + 1e-6:
                warnings.append("%s: framing_target keys are sparser than key_step_s %s (key densely, assert the projected quantity in the sweep)" % (s.get("id"), ft.get("key_step_s", 0.1)))
        for wa in s.get("world_anchors", []) or []:
            hl = wa.get("hold_line_frac")
            if hl is not None and not (0 < hl < 1):
                errors.append("%s: world_anchors %s hold_line_frac must be in (0, 1)" % (s.get("id"), wa.get("id")))
    rd = (proj.get("camera") or {}).get("rest_drift") or {}
    if rd.get("shape", "ellipse") == "ellipse" and rd:
        for k in ("lateral_units", "vertical_units", "omega_rad_s"):
            if rd.get(k) is None:
                errors.append("project.camera.rest_drift: %s is required for an ellipse" % k)
        if rd.get("vertical_units") == 0:
            errors.append("project.camera.rest_drift: vertical_units 0 is a one-axis sway (still at every turning point)")
    for b in rd.get("boosts", []) or []:
        if b.get("to_s", 0) > dur + 1e-6 or b.get("from_s", 0) > b.get("to_s", 0):
            errors.append("project.camera.rest_drift.boosts: window %s-%s is outside the film or reversed" % (b.get("from_s"), b.get("to_s")))
    sil = (spec.get("audio") or {}).get("silence") or []
    for w in sil:
        if len(w) != 2 or w[0] >= w[1] or w[1] > dur + 1e-6:
            errors.append("audio.silence: window %s is reversed or outside the film" % (w,))
    g = proj.get("gates") or {}
    if g.get("hyperframes_cmd") not in (None, "npx hyperframes"):
        errors.append("project.gates.hyperframes_cmd must be 'npx hyperframes' (run_gates splits a path on spaces)")
    for var in proj.get("variants", []) or []:
        comp = var.get("composition", "")
        if comp and not os.path.exists(os.path.join(spec_dir, comp)):
            warnings.append("variant %s: %s does not exist yet (stage 6 builds it; it is gated on its own render)" % (var.get("id"), comp))
    mo = (spec.get("audio") or {}).get("music_only") or {}
    if mo.get("stem") and not os.path.exists(os.path.join(spec_dir, mo["stem"])):
        warnings.append("audio.music_only.stem %s does not exist yet (stage 8; master it with synth_sfx.py --master-stem before the mux)" % mo["stem"])
    for w in warnings:
        print("  warning: " + w)
    if errors:
        print("INVALID: %s (%d problems)" % (a.spec, len(errors)))
        for e in errors[:50]:
            print("  - " + e)
        sys.exit(1)
    print("valid: %s (worldfilm %s over shotspec %s; %d shots)" % (a.spec, wf["$id"].rsplit("/", 1)[-1], ss["$id"].rsplit("/", 1)[-1], len(shots)))


if __name__ == "__main__":
    main()
