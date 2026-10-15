#!/usr/bin/env python3
"""validate_spec.py — validate a worldfilm spec against schema/worldfilm.schema.json, which extends shotspec-film's
schema/shotspec.schema.json by $ref (old ShotSpecs validate unchanged). Also checks the cross-references the schema
cannot:
  - every shots[].world_anchors[].text_id exists in that shot's text[]; hold_line_frac is inside (0, 1)
  - camera poses are sorted and inside their shot; project.camera.dial is set when any shot carries poses
  - framing_target keys are sorted, inside the shot, keyed at key_step_s or denser (warning), hold after the last key
  - rest drift: an ellipse names its lateral / vertical / omega parameters and is not one-axis; boosts lie inside the film
  - audio: cue event bindings are unique; silence windows are ordered and inside the film
  - gates: the runner command is "npx hyperframes"; hard cuts, pops allowances and the poster time lie inside the film
  - variants: ids are unique file-name slugs; (warnings) compositions and the music-only stem exist
  - (warning) shots at or above rest_drift.min_dial have no rest drift configured, so their rests may read as frozen

usage: validate_spec.py shotspec.json [--schema schema/worldfilm.schema.json] [--shotspec-schema <path>]
exit 0 valid, 1 invalid, 2 usage / dependency error
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EPS = 1e-6
SLUG = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")


def find_shotspec_schema(explicit):
    cands = [explicit, os.environ.get("SHOTSPEC_HOME", "") and os.path.join(os.environ["SHOTSPEC_HOME"], "schema", "shotspec.schema.json"),
             os.path.join(HERE, "..", "..", "studio", "kits", "shotspec-film", "schema", "shotspec.schema.json"),
             os.path.expanduser("~/.codex/skills/shotspec-film/schema/shotspec.schema.json")]
    for c in cands:
        if c and os.path.exists(c):
            return os.path.abspath(c)
    return None


def num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def cross_checks(spec, spec_dir):
    errors, warnings = [], []
    proj = spec.get("project", {}) or {}
    shots = spec.get("shots", []) or []
    dur = float(proj.get("duration") or 0)
    pcam = proj.get("camera") or {}
    rd = pcam.get("rest_drift") or {}
    has_cam = False

    for s in shots:
        sid = s.get("id")
        t_in, t_out = s.get("t_in"), s.get("t_out")
        texts = {t.get("id") for t in s.get("text", []) or []}
        for wa in s.get("world_anchors", []) or []:
            if wa.get("text_id") and wa["text_id"] not in texts:
                errors.append("%s: world_anchors %s refers to text_id %r not in this shot's text[]" % (sid, wa.get("id"), wa.get("text_id")))
            hl = wa.get("hold_line_frac")
            if hl is not None and not (0 < hl < 1):
                errors.append("%s: world_anchors %s hold_line_frac must be in (0, 1)" % (sid, wa.get("id")))
        cam = s.get("camera") or {}
        poses = cam.get("poses") or []
        if poses:
            has_cam = True
            ts = [p.get("t") for p in poses]
            if all(num(t) for t in ts):
                if ts != sorted(ts):
                    errors.append("%s: camera poses are not sorted in time" % sid)
                if num(t_in) and num(t_out) and (ts[0] < t_in - EPS or ts[-1] > t_out + EPS):
                    errors.append("%s: camera poses outside [t_in, t_out]" % sid)
        ft = cam.get("framing_target")
        if ft:
            kt = [k[0] for k in ft.get("keys", []) or [] if isinstance(k, list) and k and num(k[0])]
            if kt != sorted(kt):
                errors.append("%s: framing_target keys are not sorted in time" % sid)
            if kt and num(t_in) and num(t_out) and (kt[0] < t_in - EPS or kt[-1] > t_out + EPS):
                errors.append("%s: framing_target keys outside [t_in, t_out]" % sid)
            if kt and ft.get("hold_from_s") is not None and ft["hold_from_s"] < kt[-1] - EPS:
                errors.append("%s: framing_target.hold_from_s is before its last key" % sid)
            step = float(ft.get("key_step_s", 0.1))
            if len(kt) > 1 and max(b - a for a, b in zip(kt, kt[1:])) > step + EPS:
                warnings.append("%s: framing_target keys are sparser than key_step_s %s (key densely, assert the projected quantity in the sweep)" % (sid, step))
        fl = s.get("footage_layer")
        if fl and not os.path.isdir(os.path.join(spec_dir, fl.get("mask_dir", ""))):
            errors.append("%s: footage_layer.mask_dir %r does not exist" % (sid, fl.get("mask_dir")))

    if has_cam and "dial" not in pcam:
        errors.append("project.camera.dial must be set when any shot carries camera poses")

    shape = rd.get("shape", "ellipse") if rd else "none"
    if shape == "ellipse":
        for k in ("lateral_units", "vertical_units", "omega_rad_s"):
            if rd.get(k) is None:
                errors.append("project.camera.rest_drift: %s is required for an ellipse" % k)
        if rd.get("vertical_units") == 0:
            errors.append("project.camera.rest_drift: vertical_units 0 is a one-axis sway (still at every turning point)")
        if rd.get("slow_lateral_units") and rd.get("slow_omega_rad_s") is None:
            errors.append("project.camera.rest_drift: slow_lateral_units needs slow_omega_rad_s")
    for b in rd.get("boosts", []) or []:
        if b.get("from_s", 0) > b.get("to_s", 0) or b.get("from_s", 0) < -EPS or b.get("to_s", 0) > dur + EPS:
            errors.append("project.camera.rest_drift.boosts: window %s-%s is outside the film or reversed" % (b.get("from_s"), b.get("to_s")))
    if "dial" in pcam and shape != "ellipse":
        min_dial = int(rd.get("min_dial", 3)) if rd else 3
        drifting = [s.get("id") for s in shots if (s.get("camera") or {}).get("poses") and int((s.get("camera") or {}).get("dial", pcam["dial"])) >= min_dial]
        if drifting:
            warnings.append("no rest drift configured for shots at dial >= %d (%s): rests there may read as frozen; configure project.camera.rest_drift or confirm the shots never rest" % (min_dial, ", ".join(map(str, drifting[:6]))))

    audio = spec.get("audio") or {}
    events = [c.get("event") for c in audio.get("cues") or [] if c.get("event")]
    if len(events) != len(set(events)):
        errors.append("audio.cues: duplicate event bindings %s" % sorted({e for e in events if events.count(e) > 1}))
    for w in audio.get("silence") or []:
        if len(w) != 2 or w[0] >= w[1] or w[0] < -EPS or w[1] > dur + EPS:
            errors.append("audio.silence: window %s is reversed or outside the film" % (w,))

    g = proj.get("gates") or {}
    if g.get("hyperframes_cmd") not in (None, "npx hyperframes"):
        errors.append("project.gates.hyperframes_cmd must be 'npx hyperframes' (run_gates splits a path on spaces)")
    for key in ("hard_cuts_s", "pops_allow_s"):
        for t in g.get(key) or []:
            if t < -EPS or t > dur + EPS:
                errors.append("project.gates.%s: %s is outside the film" % (key, t))
    if g.get("cta_tail_s") is not None and g["cta_tail_s"] > dur + EPS:
        errors.append("project.gates.cta_tail_s is longer than the film")
    poster = (proj.get("delivery") or {}).get("poster_t")
    if poster is not None and poster > dur + EPS:
        errors.append("project.delivery.poster_t %s is outside the film" % poster)

    ids = []
    for var in proj.get("variants", []) or []:
        vid = var.get("id", "")
        ids.append(vid)
        if vid and not SLUG.match(vid):
            errors.append("variant %r: id must be a lowercase file-name slug (it names renders and gate folders)" % vid)
        comp = var.get("composition", "")
        if comp and not os.path.exists(os.path.join(spec_dir, comp)):
            warnings.append("variant %s: %s does not exist yet (build it before rendering; it is gated on its own render)" % (vid, comp))
    if len(ids) != len(set(ids)):
        errors.append("project.variants: duplicate ids %s" % sorted({i for i in ids if ids.count(i) > 1}))
    mo = audio.get("music_only") or {}
    if mo.get("stem") and not os.path.exists(os.path.join(spec_dir, mo["stem"])):
        warnings.append("audio.music_only.stem %s does not exist yet (master it with synth_sfx.py --master-stem before the mux)" % mo["stem"])
    return errors, warnings


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
    try:
        wf = json.load(open(a.schema))
        ss = json.load(open(base))
        spec = json.load(open(a.spec))
    except (OSError, ValueError) as e:
        print("cannot read input: %s" % e)
        sys.exit(2)
    registry = Registry().with_resources([(ss["$id"], Resource.from_contents(ss)), (wf["$id"], Resource.from_contents(wf))])
    v = jsonschema.Draft202012Validator(wf, registry=registry)
    errors = ["schema: %s: %s" % ("/".join(str(p) for p in e.absolute_path) or "<root>", e.message)
              for e in sorted(v.iter_errors(spec), key=lambda e: [str(p) for p in e.absolute_path])]
    try:
        more, warnings = cross_checks(spec, os.path.dirname(os.path.abspath(a.spec)))
        errors += more
    except (TypeError, ValueError, KeyError, AttributeError) as e:   # malformed shapes the schema already reported
        if not errors:
            raise
        warnings = ["cross-checks stopped on the schema errors above (%s)" % e]
    for w in warnings:
        print("  warning: " + w)
    if errors:
        print("INVALID: %s (%d problems)" % (a.spec, len(errors)))
        for e in errors[:50]:
            print("  - " + e)
        sys.exit(1)
    print("valid: %s (worldfilm %s over shotspec %s; %d shots)" % (a.spec, wf["$id"].rsplit("/", 1)[-1], ss["$id"].rsplit("/", 1)[-1], len(spec.get("shots", []))))


if __name__ == "__main__":
    main()
