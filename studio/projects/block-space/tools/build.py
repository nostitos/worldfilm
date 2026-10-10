#!/usr/bin/env python3
"""tools/build.py — "Block Space": one source for the data, the facts, the Shot Spec and the browser constants.

Reads data/schedule.csv (Bitcoin issuance schedule: heights, subsidies, header-time years, coins issued before each
halving; retained from the "21,000,000" project, sources in references/sources/) and writes:
  data/periods.csv   one row per 2,016-block difficulty period from block 0 to the last subsidy block (6,929,999)
  facts.json         every number that reaches the screen, with its source
  shotspec.json      the worldfilm Shot Spec (shots, camera pose graph, labels, captions, audio cue summary)
  film/data.js       the same timeline for the browser (world.js / film.js read nothing else)
Run: python3 tools/build.py
"""
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)

FPS, DUR, BPM = 60, 30.0, 120
BEAT = 60.0 / BPM
PERIOD = 2016
LAST_SUBSIDY_BLOCK = 6929999
TIP = 970440                      # block height at retrieval (2026-10-08 04:41:49 UTC)
TIP_YEAR = 2026.76766
RETRIEVED = "2026-10-08"

# ------------------------------------------------------------------------------------------------ data
sched = list(csv.DictReader(open("data/schedule.csv")))
halvings = [r for r in sched if r["note"] == "halving"]
by_height = {int(r["height"]): r for r in sched}


def subsidy_sats(h):
    """Block subsidy in satoshi exactly as GetBlockSubsidy computes it: 50 BTC right-shifted once per halving, truncating."""
    k = h // 210000
    return 0 if k >= 64 else (5000000000 >> k)


def subsidy_at(h):
    return subsidy_sats(h) / 1e8


def fmt_sats(sats):
    """Exact BTC text for an integer satoshi amount (no float rounding): 76293 -> 0.00076293."""
    return "%d.%08d" % (sats // 100000000, sats % 100000000)


def year_at(h):
    """Header-time years for the past (interpolated between the measured points), 10-minute spacing after the tip."""
    if h >= TIP:
        return TIP_YEAR + (h - TIP) * 10 / 60 / 24 / 365.25
    pts = [(int(r["height"]), float(r["year"])) for r in sched if r["past"] == "True"]
    pts.sort()
    for (h0, y0), (h1, y1) in zip(pts, pts[1:]):
        if h0 <= h < h1:
            return y0 + (y1 - y0) * (h - h0) / (h1 - h0)
    return pts[-1][1]


def coins_before(h):
    """Coins issued before block h, from the schedule (exact in integer satoshi arithmetic, as Bitcoin Core does it)."""
    total = 0
    sat = 50 * 100000000
    k = 0
    while True:
        a, b = k * 210000, (k + 1) * 210000
        if h <= a:
            break
        total += (min(h, b) - a) * (sat >> k)
        k += 1
        if (sat >> k) == 0:
            break
    return total / 1e8


periods = []
n_periods = LAST_SUBSIDY_BLOCK // PERIOD + 1  # 3438: the last period is partial (ends at 6,929,999)
for i in range(n_periods):
    h0 = i * PERIOD
    h1 = min(h0 + PERIOD - 1, LAST_SUBSIDY_BLOCK)
    periods.append({"period": i, "start_height": h0, "end_height": h1, "subsidy": fmt_sats(subsidy_sats(h0)), "subsidy_sats": subsidy_sats(h0), "year_est": round(year_at(h0), 5),
                    "coins_before": round(coins_before(h0), 8), "past": h0 <= TIP, "halving_k": (h0 // 210000) if h0 % 210000 < PERIOD and h0 > 0 else ""})
with open("data/periods.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(periods[0].keys()))
    w.writeheader()
    w.writerows(periods)

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
BLOCK_TIMES = json.load(open("references/sources/blockstream_block_timestamps.json"))


def month_year(h):
    utc = BLOCK_TIMES[str(h)]["utc"]
    return "%s %s" % (MONTHS[int(utc[5:7]) - 1], utc[:4])


def fmt_int(n):
    return "{:,}".format(int(n))


def fmt_btc(x):
    s = ("%.8f" % x).rstrip("0").rstrip(".")
    return s


# ------------------------------------------------------------------------------------------------ facts
SRC_CORE = "references/sources/bitcoin_commit.txt (Bitcoin Core db0bde16b910: validation.cpp GetBlockSubsidy, chainparams.cpp nSubsidyHalvingInterval / DifficultyAdjustmentInterval)"
SRC_TIMES = "references/sources/blockstream_block_timestamps.json"
facts = {
    "F-RULE": {"claim": "The block subsidy starts at 50 coins (5,000,000,000 satoshi) and is right-shifted (halved, truncating to whole satoshi) every 210,000 blocks.", "value": {"subsidy0": 50, "subsidy0_sats": 5000000000, "halving_interval": 210000}, "kind": "measurement",
               "source": SRC_CORE, "url": "https://github.com/bitcoin/bitcoin/blob/master/src/validation.cpp", "retrieved": RETRIEVED, "display": ["50", "210,000"]},
    "F-PERIOD": {"claim": "The difficulty adjusts every 2,016 blocks (two weeks at ten minutes a block): one building per period.", "value": 2016, "kind": "measurement",
                 "source": SRC_CORE, "url": "https://github.com/bitcoin/bitcoin/blob/master/src/chainparams.cpp", "retrieved": RETRIEVED, "display": ["2,016", "2016"]},
    "F-GENESIS": {"claim": "Block 0 (the genesis block) has header time 2009-01-03 18:15:05 UTC; its subsidy was 50 coins.", "value": {"height": 0, "utc": BLOCK_TIMES["0"]["utc"], "subsidy": 50},
                  "kind": "measurement", "source": SRC_TIMES, "url": "https://blockstream.info/api/block-height/0", "retrieved": RETRIEVED, "display": ["0", "JAN 2009", "2009", "50"]},
}
for k, h in enumerate((210000, 420000, 630000, 840000), start=1):
    facts["F-H%d" % k] = {"claim": "Halving %d at block %s (%s): the subsidy fell to %s coins; %s coins had been issued before it." % (k, fmt_int(h), BLOCK_TIMES[str(h)]["utc"], fmt_btc(subsidy_at(h)), fmt_btc(coins_before(h))),
                          "value": {"height": h, "utc": BLOCK_TIMES[str(h)]["utc"], "subsidy": subsidy_at(h), "coins_before": coins_before(h)}, "kind": "measurement",
                          "source": SRC_TIMES + "; " + SRC_CORE, "url": "https://blockstream.info/api/block-height/%d" % h, "retrieved": RETRIEVED,
                          "display": [fmt_int(h), month_year(h), str(int(BLOCK_TIMES[str(h)]["utc"][:4])), fmt_btc(subsidy_at(h)), fmt_int(int(coins_before(h)))]}
SO_FAR = coins_before(TIP + 1)   # issued through the tip block, inclusive ("so far"); before the tip block it is 20,095,125
facts["F-NOW"] = {"claim": "At retrieval the chain tip was block %s (header time %s UTC); %s coins had been issued through it (%s before it); the subsidy is 3.125 coins." % (
                      fmt_int(TIP), BLOCK_TIMES[str(TIP)]["utc"], fmt_btc(SO_FAR), fmt_btc(coins_before(TIP))),
                  "value": {"height": TIP, "utc": BLOCK_TIMES[str(TIP)]["utc"], "coins_through_tip": SO_FAR, "coins_through_tip_whole": int(SO_FAR), "coins_before_tip": coins_before(TIP), "subsidy": 3.125}, "kind": "measurement",
                  "source": SRC_TIMES, "url": "https://blockstream.info/api/blocks/tip/height", "retrieved": RETRIEVED, "display": [fmt_int(TIP), "OCT 2026", "2026", fmt_int(int(SO_FAR)), "3.125"]}
future = [r for r in halvings if r["past"] == "False"]
facts["F-FUTURE"] = {"claim": "28 more halvings remain with a non-zero subsidy (blocks 1,050,000 to 6,720,000: 1.5625 coins down to 1 satoshi); their dates assume ten-minute blocks and are estimates.",
                     "value": {"count": len(future), "first": {"k": 5, "height": 1050000, "subsidy": 1.5625, "year_est": round(year_at(1050000), 2)}, "heights": [int(r["height"]) for r in future]},
                     "kind": "projection", "source": "data/schedule.csv (derived from F-RULE); dates: ten-minute spacing from the tip", "url": "", "retrieved": RETRIEVED,
                     "display": ["28", "5", "1,050,000", "1.5625", "2028", "6,720,000"]}
facts["F-LAST"] = {"claim": "Block 6,929,999 is the last block with a subsidy (1 satoshi); from block 6,930,000 the subsidy is 0. At ten minutes a block that is around the year 2140.",
                   "value": {"height": LAST_SUBSIDY_BLOCK, "year_est": round(year_at(LAST_SUBSIDY_BLOCK), 2)}, "kind": "projection", "source": SRC_CORE + "; data/schedule.csv", "url": "", "retrieved": RETRIEVED,
                   "display": ["6,929,999", "2140", "0", "0.00000001"]}
facts["F-CAP"] = {"claim": "The schedule sums to 20,999,999.9769 coins: 21,000,000 when rounded (the v0.1 announcement: \"Total circulation will be 21,000,000 coins\"); Bitcoin Core MAX_MONEY = 21,000,000 is a validity bound.",
                  "value": 21000000, "kind": "measurement", "source": SRC_CORE + "; metzdowd cryptography list, 2009-01-08", "url": "https://www.metzdowd.com/pipermail/cryptography/2009-January/014994.html",
                  "retrieved": RETRIEVED, "schedule_sum": 20999999.9769, "display": ["21,000,000", "20,999,999.9769"]}
facts["F-SERIES"] = {"claim": "One row per difficulty period (3,438 periods from block 0 to 6,929,999): data/periods.csv, derived from F-RULE, F-PERIOD and the measured block times.",
                     "value": "data/periods.csv", "kind": "measurement", "source": "tools/build.py", "url": "", "retrieved": RETRIEVED, "display": ["3,438"]}
json.dump(facts, open("facts.json", "w"), indent=1)

# ------------------------------------------------------------------------------------------------ timeline
# world units: one period = 1 unit along x; building height = subsidy * HS
HS = 0.22
U = 1.0
def px(h):            # x position of a block height along the boulevard
    return h / PERIOD * U

NOW_X = px(TIP)
END_X = px(LAST_SUBSIDY_BLOCK)
H1, H2, H3, H4 = px(210000), px(420000), px(630000), px(840000)

# shots: continuous camera (dial 4), beats every 0.5 s. Poses: {t, x (along), y (height, log-keyed), z (lateral), ahead (look distance), fov}
# Round 1 (critic): the camera rides above the roof line so every step is visible, eases to a near-stop at gate 1 (the
# 50 -> 25 step in one frame), truly stops at NOW, and the street ends. Labels are two fields, one at a time.
TOP50 = 50 * HS   # 11.0: the first epoch's roof line
shots = [
    {"id": "s01", "t_in": 0.0, "t_out": 3.0, "purpose": "cold open: the genesis slab and the canyon of the first epoch, already moving; the rule in one caption", "card": "opening/world-establish",
     "mechanism": "foreground fly-through", "style_move": "crane settle toward the roof line", "signature": True, "subject": {"what": "the genesis slab and the first epoch", "fill_ratio": 0.7, "layout": "wide"},
     "camera": {"move": "crane-down", "poses": [{"t": 0.0, "x": -18.0, "y": 24.0, "z": 4.0, "ahead": 18.0, "fov": 44}, {"t": 3.0, "x": 14.0, "y": TOP50 + 6.0, "z": 1.0, "ahead": 60.0, "fov": 48}], "velocity_peak_s": 1.3, "settle_s": 2.8},
     "text": [{"id": "C1", "content": "EVERY 2,016 BLOCKS, ONE BUILDING. ITS HEIGHT: THE NEW COINS IN EACH BLOCK.", "fact_ids": ["F-PERIOD", "F-RULE"], "role": "caption", "at_s": 0.3, "until_s": 6.5, "min_hold_s": 6.2}],
     "world_anchors": [],
     "transition_out": {"type": "continuous", "duration_s": 0, "on_beat": 6}},
    {"id": "s02", "t_in": 3.0, "t_out": 7.0, "purpose": "the first epoch above the roof line; the camera gathers speed then eases to a near-stop at the first gate: 50 next to 25 in one frame, on the kick", "card": "travel/dolly-through",
     "mechanism": "continuous canvas", "style_move": "dolly, ease to near-stop at the gate", "signature": True, "subject": {"what": "the 50-coin roof line meeting the 25-coin one", "fill_ratio": 0.8, "layout": "close"},
     "camera": {"move": "dolly-profile", "poses": [{"t": 3.0, "x": 14.0, "y": TOP50 + 6.0, "z": 1.0, "ahead": 60.0, "fov": 48}, {"t": 5.3, "x": H1 - 18.0, "y": TOP50 + 6.0, "z": 5.0, "ahead": 18.0, "fov": 50}, {"t": 5.8, "x": H1 - 7.0, "y": TOP50 + 15.0, "z": 17.0, "look_at": [H1, 5.0, 0.0], "fov": 48}, {"t": 7.0, "x": H1 - 5.5, "y": TOP50 + 14.0, "z": 16.0, "look_at": [H1 + 0.5, 5.0, 0.0], "fov": 48}], "velocity_peak_s": 5.2, "settle_s": 6.4},
     "text": [{"id": "L-h1", "content": "HALVING 1 · 25 BTC", "fact_ids": ["F-H1"], "role": "label", "at_s": 3.8, "until_s": 7.1, "min_hold_s": 3.3}],
     "world_anchors": [{"id": "A-h1", "anchor": "halving-1", "text_id": "L-h1", "offset_px": [300, -60], "occlusion": "fade"}],
     "transition_out": {"type": "continuous", "duration_s": 0, "on_beat": 14}},
    {"id": "s03", "t_in": 7.0, "t_out": 10.0, "purpose": "second epoch: through gate 1 and down the 25-coin street; halving 2 on the kick", "card": "travel/dolly-through",
     "mechanism": "continuous canvas", "style_move": "dolly, lateral drift", "signature": False, "subject": {"what": "the 25-coin street", "fill_ratio": 0.75, "layout": "close"},
     "camera": {"move": "dolly", "poses": [{"t": 7.0, "x": H1 - 5.5, "y": TOP50 + 14.0, "z": 16.0, "look_at": [H1 + 0.5, 5.0, 0.0], "fov": 48}, {"t": 7.7, "x": H1 + 8.0, "y": 25 * HS + 6.0, "z": 1.2, "ahead": 22.0, "fov": 52}, {"t": 10.0, "x": H2 - 7.5, "y": 25 * HS + 4.0, "z": -1.2, "ahead": 16.0, "fov": 52}], "velocity_peak_s": 8.6, "settle_s": 9.7},
     "text": [{"id": "L-h2", "content": "HALVING 2 · 12.5 BTC", "fact_ids": ["F-H2"], "role": "label", "at_s": 7.2, "until_s": 10.1, "min_hold_s": 2.9}],
     "world_anchors": [{"id": "A-h2", "anchor": "halving-2", "text_id": "L-h2", "offset_px": [0, -28], "occlusion": "fade"}],
     "transition_out": {"type": "continuous", "duration_s": 0, "on_beat": 20}},
    {"id": "s04", "t_in": 10.0, "t_out": 13.0, "purpose": "third epoch at 12.5: the slabs are a quarter of the first; halving 3 on the kick", "card": "travel/dolly-through",
     "mechanism": "continuous canvas", "style_move": "dolly, lower", "signature": False, "subject": {"what": "the 12.5-coin street", "fill_ratio": 0.7, "layout": "close"},
     "camera": {"move": "dolly-swell", "poses": [{"t": 10.0, "x": H2 - 7.5, "y": 25 * HS + 4.0, "z": -1.2, "ahead": 16.0, "fov": 52}, {"t": 11.4, "x": H2 + 52.0, "y": 25 * HS + 1.0, "z": 0.4, "ahead": 12.0, "fov": 54}, {"t": 13.0, "x": H3 - 7.5, "y": 12.5 * HS + 2.4, "z": 1.1, "ahead": 14.0, "fov": 54}], "velocity_peak_s": 11.0, "settle_s": 12.7},
     "text": [{"id": "L-h3", "content": "HALVING 3 · 6.25 BTC", "fact_ids": ["F-H3"], "role": "label", "at_s": 10.1, "until_s": 13.0, "min_hold_s": 2.9}],
     "world_anchors": [{"id": "A-h3", "anchor": "halving-3", "text_id": "L-h3", "offset_px": [0, -28], "occlusion": "fade"}],
     "transition_out": {"type": "continuous", "duration_s": 0, "on_beat": 26}},
    {"id": "s05", "t_in": 13.0, "t_out": 15.5, "purpose": "fourth epoch at 6.25: walls, not towers; halving 4 on the kick", "card": "travel/dolly-through",
     "mechanism": "continuous canvas", "style_move": "dolly, faster", "signature": False, "subject": {"what": "the 6.25-coin street", "fill_ratio": 0.65, "layout": "close"},
     "camera": {"move": "dolly", "poses": [{"t": 13.0, "x": H3 - 7.5, "y": 12.5 * HS + 2.4, "z": 1.1, "ahead": 14.0, "fov": 54}, {"t": 15.5, "x": H4 - 7.5, "y": 6.25 * HS + 2.6, "z": -0.9, "ahead": 14.0, "fov": 56}], "velocity_peak_s": 14.3, "settle_s": 15.3},
     "text": [{"id": "L-h4", "content": "HALVING 4 · 3.125 BTC", "fact_ids": ["F-H4"], "role": "label", "at_s": 13.0, "until_s": 15.65, "min_hold_s": 2.65}],
     "world_anchors": [{"id": "A-h4", "anchor": "halving-4", "text_id": "L-h4", "offset_px": [0, -28], "occlusion": "fade"}],
     "transition_out": {"type": "continuous", "duration_s": 0, "on_beat": 31}},
    {"id": "s06", "t_in": 15.5, "t_out": 19.5, "purpose": "the present: the camera arrives at block 970,440 and stops (drift only) for two seconds; the issued supply so far is the one number held", "card": "reveal/arrive-and-hold",
     "mechanism": "object as landmark", "style_move": "stop with micro-drift", "signature": True, "subject": {"what": "the NOW gate at block 970,440", "fill_ratio": 0.7, "layout": "wide"},
     "camera": {"move": "stop", "poses": [{"t": 15.5, "x": H4 - 7.5, "y": 6.25 * HS + 2.6, "z": -0.9, "ahead": 14.0, "fov": 56}, {"t": 17.4, "x": NOW_X - 8.0, "y": 4.0, "z": 0.9, "ahead": 8.0, "fov": 52}, {"t": 19.3, "x": NOW_X - 8.0, "y": 4.0, "z": 0.9, "ahead": 8.0, "fov": 52}], "velocity_peak_s": 16.0, "settle_s": 17.4},
     "text": [{"id": "L-now", "content": "NOW · BLOCK 970,440 · OCT 2026", "fact_ids": ["F-NOW"], "role": "label", "at_s": 16.3, "until_s": 19.8, "min_hold_s": 3.5},
              {"id": "C2", "content": "20,095,128 COINS ISSUED SO FAR.", "fact_ids": ["F-NOW"], "role": "caption", "at_s": 16.2, "until_s": 19.5, "min_hold_s": 3.3}],
     "world_anchors": [{"id": "A-now", "anchor": "now", "text_id": "L-now", "offset_px": [0, -28], "occlusion": "always"}],
     "transition_out": {"type": "continuous", "duration_s": 0, "on_beat": 39}},
    {"id": "s07", "t_in": 19.5, "t_out": 23.0, "purpose": "the written future: the camera cranes up and races along 28 more halvings as the slabs thin to hairlines", "card": "travel/crane-race",
     "mechanism": "scale collapse", "style_move": "crane up, accelerate, log-space pull", "signature": True, "subject": {"what": "the thinning schedule to 2140", "fill_ratio": 0.8, "layout": "overhead"},
     "camera": {"move": "crane-race", "poses": [{"t": 19.5, "x": NOW_X - 8.0, "y": 4.0, "z": 0.9, "ahead": 8.0, "fov": 52}, {"t": 20.8, "x": NOW_X + 50.0, "y": 30.0, "z": 5.0, "ahead": 260.0, "fov": 50}, {"t": 21.5, "x": NOW_X + 900.0, "y": 34.0, "z": 2.0, "ahead": 350.0, "fov": 51},
                                              ], "velocity_peak_s": 21.9, "settle_s": 23.0},
     "text": [{"id": "C3", "content": "28 MORE HALVINGS STILL PAY OUT.", "fact_ids": ["F-FUTURE"], "role": "caption", "at_s": 19.6, "until_s": 23.2, "min_hold_s": 3.6},
              {"id": "L-h5", "content": "HALVING 5 · 1.5625 BTC", "fact_ids": ["F-FUTURE"], "role": "projection", "at_s": 19.9, "until_s": 22.9, "min_hold_s": 3.0}],
     "world_anchors": [{"id": "A-h5", "anchor": "halving-5", "text_id": "L-h5", "offset_px": [0, -28], "occlusion": "fade"}],
     "transition_out": {"type": "continuous", "duration_s": 0, "on_beat": 46}},
    {"id": "s08", "t_in": 23.0, "t_out": 27.0, "purpose": "the end of the schedule: one hairline running out to the last block, seen from the street axis; the ground's edge settles in the top fifth; two seconds of digital silence", "card": "reveal/overhead-end",
     "mechanism": "object as landmark", "style_move": "settle, pitched; drift through the silence", "signature": False, "subject": {"what": "the last subsidy block and the void after it", "fill_ratio": 0.6, "layout": "overhead"},
     "camera": {"move": "settle-pitched", "poses": [], "velocity_peak_s": 23.8, "settle_s": 25.0},
     "text": [{"id": "C4", "content": "THE LAST NEW COIN.", "fact_ids": ["F-LAST"], "role": "caption", "at_s": 24.1, "until_s": 26.95, "min_hold_s": 2.85},
              {"id": "L-last", "content": "LAST BLOCK · 6,929,999", "fact_ids": ["F-LAST"], "role": "projection", "at_s": 23.8, "until_s": 26.9, "min_hold_s": 3.1}],
     "world_anchors": [{"id": "A-last", "anchor": "last", "text_id": "L-last", "offset_px": [0, -40], "occlusion": "always"}],
     "transition_out": {"type": "continuous", "duration_s": 0, "on_beat": 54}},
    {"id": "s09", "t_in": 27.0, "t_out": 30.0, "purpose": "payoff after the silence: the cap, loudest moment of the film, with a slow dolly in under the number (the edge holds still)", "card": "closing/number-card",
     "mechanism": "full-frame type", "style_move": "slow dolly under the number", "signature": False, "subject": {"what": "21,000,000", "fill_ratio": 0.6, "layout": "full-frame-type"},
     "camera": {"move": "push", "poses": [], "velocity_peak_s": 28.3, "settle_s": 27.0},
     "text": [{"id": "H-cap", "content": "21,000,000", "fact_ids": ["F-CAP"], "role": "headline", "at_s": 27.0, "until_s": 30.0, "min_hold_s": 3.0},
              {"id": "K-cap", "content": "NEVER MORE.", "fact_ids": [], "role": "kicker", "at_s": 27.3, "until_s": 30.0, "min_hold_s": 2.7},
              {"id": "X-cap", "content": "20,999,999.9769 BTC", "fact_ids": ["F-CAP"], "role": "note", "at_s": 27.1, "until_s": 30.0, "min_hold_s": 2.9}],
     "world_anchors": [],
     "transition_out": {"type": "end", "duration_s": 0}},
]

# ---- the end stretch (23.0-30.0): keys every 0.5 s. The camera rides the street axis; its look direction is SOLVED
# from a target curve for where the ground's end edge sits on screen (fraction from the top), so the edge settles in
# one direction and holds still under the number (critic r7). The look target's x climbs to just past the end, so the
# readout (block at the look point, clamped to the chain) climbs to 6,929,999 and stays.
def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

def lerp_path(t, pts):
    for (t0, a), (t1, b) in zip(pts, pts[1:]):
        if t0 <= t <= t1:
            u = smooth((t - t0) / (t1 - t0)) if t1 > t0 else 0
            return [a[i] + (b[i] - a[i]) * u for i in range(len(a))]
    return list(pts[-1][1])

POS = [(22.3, [END_X - 125.0, 52.0]), (22.6, [END_X - 95.0, 46.0]), (23.0, [END_X - 60.0, 40.0]), (25.0, [END_X - 32.0, 13.0]), (27.0, [END_X - 23.5, 9.8]), (30.0, [END_X - 17.0, 6.0])]
EDGE = [(22.3, [0.045]), (22.6, [0.06]), (23.0, [0.08]), (25.0, [0.19]), (27.0, [0.21]), (30.0, [0.21])]
FOVK = [(22.3, [52.0]), (22.6, [52.0]), (23.0, [52.0]), (25.0, [44.0]), (30.0, [44.0])]
TGTX = [(22.3, [END_X - 55.0]), (22.6, [END_X - 45.0]), (23.0, [END_X - 30.0]), (25.0, [END_X + 8.0]), (30.0, [END_X + 8.0])]

def end_pose(t):
    px, py = lerp_path(t, POS)
    yfrac = lerp_path(t, EDGE)[0]
    fov = lerp_path(t, FOVK)[0]
    tx = lerp_path(t, TGTX)[0]
    phi = math.atan2(py, END_X - px)                              # depression of the end point
    alpha = math.atan((0.5 - yfrac) * 2 * math.tan(math.radians(fov) / 2))   # end point this far above the frame centre
    theta = phi + alpha                                            # camera pitch (down)
    ly = py - (tx - px) * math.tan(theta)
    return {"t": round(t, 3), "x": round(px, 4), "y": round(py, 4), "z": 0.0, "look_at": [round(tx, 4), round(ly, 4), 0.0], "fov": round(fov, 3)}

shots[7]["camera"]["poses"] = [end_pose(23.0 + 0.1 * i) for i in range(41)]         # 23.0 .. 27.0, every 0.1 s: the cubic cannot deviate between keys
shots[8]["camera"]["poses"] = [end_pose(27.0 + 0.1 * i) for i in range(31)]         # 27.0 .. 30.0
shots[6]["camera"]["poses"] += [end_pose(22.3 + 0.1 * i) for i in range(8)]       # 22.3 .. 23.0: the solved curve begins before the bracket enters the frame

beat_grid = [round(i * BEAT, 4) for i in range(int(DUR / BEAT) + 1)]

# rail poses -> schema poses: pos = [x, y, z] on the boulevard, look = the ground point `ahead` units down the street
for s in shots:
    for p in s["camera"]["poses"]:
        p["pos"] = [round(p["x"], 4), round(p["y"], 4), round(p["z"], 4)]
        p["look"] = [round(v, 4) for v in p["look_at"]] if "look_at" in p else [round(p["x"] + p["ahead"], 4), 0.0, 0.0]

# events the sound is locked to (times on the beat grid) — halvings in the past on kicks, future halvings accelerate
events = [{"id": "open", "t": 0.0, "kind": "open"}, {"id": "halving-1", "t": 7.0, "kind": "halving", "height": 210000}, {"id": "halving-2", "t": 10.0, "kind": "halving", "height": 420000},
          {"id": "halving-3", "t": 13.0, "kind": "halving", "height": 630000}, {"id": "halving-4", "t": 15.5, "kind": "halving", "height": 840000}, {"id": "now", "t": 17.4, "kind": "arrive"}]
# future halvings pass the camera between 19.5 and 23.5 as it races: place them on the camera's x(t) (computed in film.js); here the beat times
fut_t = [19.8, 20.25, 20.6, 20.9, 21.15, 21.35, 21.52, 21.67, 21.8, 21.92, 22.02, 22.11, 22.19, 22.26, 22.32, 22.38, 22.43, 22.48, 22.52, 22.56, 22.6, 22.64, 22.67, 22.7, 22.73, 22.76, 22.79, 22.82]
for i, t in enumerate(fut_t):
    events.append({"id": "halving-%d" % (5 + i), "t": t, "kind": "halving-future", "height": 1050000 + 210000 * i})
events += [{"id": "end", "t": 25.0, "kind": "arrive"}, {"id": "silence", "t": 25.0, "kind": "silence", "until": 27.0}, {"id": "cap", "t": 27.0, "kind": "payoff"}]

spec = {
    "spec_version": "0.1",
    "project": {
        "title": "Block Space", "fps": FPS, "duration": DUR,
        "sizes": [{"w": 1920, "h": 1080, "label": "landscape"}, {"w": 1080, "h": 1920, "label": "vertical"}],
        "audience": "people who have heard 'there will only be 21 million' and have never seen the schedule as a place",
        "cta": "none: the film ends on the number",
        "brand": {"name": "Block Space", "colors": {"ground": "#0B0D10", "concrete": "#1B1F26", "ink": "#E9E4D8", "accent": "#F7931A", "fog": "#0E1116"}, "fonts": ["IBM Plex Mono", "Newsreader"]},
        "facts_file": "facts.json",
        "style": {"id": "custom", "palette": ["#0B0D10", "#1B1F26", "#E9E4D8", "#F7931A", "#0E1116"],
                  "notes": "a night city of concrete slabs, edges drawn in bone ink, one orange accent reserved for the halving gates and the number; fog eats the far end; the future is wireframe (scheduled, not mined)"},
        "motion_tokens": {"energy": 0.7, "tone": "monumental, measured, cold", "base_duration_s": 0.5, "ease_in": "expo.out", "ease_out": "expo.in", "overshoot": 0, "no_linear": True},
        "music": {"src": "assets/mix.wav", "bpm": BPM, "beat_offset_s": 0.0, "beat_grid": beat_grid, "license": "original, synthesized: audio/cues.json via worldfilm synth_sfx.py"},
        "camera": {"dial": 4, "signature_moves": ["dolly", "crane"], "max_hold_s": 0.5, "log_space": True, "notes": "Flowing: the camera is in motion in every shot; height and look-ahead are keyed in log space; momentum hands shot to shot. The bar is tighter than the house default: hold_max_s 0.3 (the designed NOW stop measures 0.2 s), frozen_max_s_per_30s 1.0; the end card (27-30 s) is the CTA tail."},
        "reference": {"sources": ["references/engine.reference.json", "references/twenty-one-million.reference.json"], "approved": False},
        "blur": {"samples_per_frame": 4, "shutter_angle": 180, "shutter_phase": -90, "route": "playwright"},
        "world": {"module": "world.js", "kind": "three", "seed": 21, "data_files": ["data/periods.csv"], "precompute_note": "3,438 buildings (one per period) are laid out once at load into instanced geometry; render(t) only moves the camera and the labels"},
        "quality_bar": {"frozen_max_s_per_30s": 1.0, "hold_max_s": 0.3, "contrast_min": 4.5, "lufs_target": -14, "true_peak_max_dbtp": -1, "cut_error_max_frames": 2, "handoff_max_mean_abs_diff": 6, "palette_max_distance": 40},
    },
    "shots": shots,
    "audio": {"cue_sheet": "audio/cues.json", "synth_report": "gates/audio-synth.json", "silence": [[25.0, 27.0]],
              "cues": [{"id": "kick-h%d" % k, "t": t, "gen": "kick", "group": "sfx", "audibility_db": 6, "event": "halving-%d" % k} for k, t in ((1, 7.0), (2, 10.0), (3, 13.0), (4, 15.5))] +
                      [{"id": "whoosh-s01", "t": 1.3, "gen": "whoosh", "group": "sfx", "audibility_db": 4, "event": "open"},
                       {"id": "arrive-now", "t": 17.4, "gen": "blip", "group": "sfx", "audibility_db": 4, "event": "now"},
                       {"id": "riser", "t": 24.95, "gen": "riser", "group": "sfx", "audibility_db": 4, "event": "end"},
                       {"id": "impact-cap", "t": 27.0, "gen": "impact", "group": "sfx", "audibility_db": 6, "event": "cap"}]},
}
json.dump(spec, open("shotspec.json", "w"), indent=1)

data_js = {"fps": FPS, "dur": DUR, "world_seed": 21, "bpm": BPM, "beat": BEAT, "period": PERIOD, "tip": TIP, "last": LAST_SUBSIDY_BLOCK, "hs": HS, "u": U, "now_x": NOW_X, "end_x": END_X,
           "halving_x": {str(k): px(210000 * k) for k in range(1, 34)}, "shots": shots, "events": events, "colors": spec["project"]["brand"]["colors"],
           "periods": [[p["period"], p["subsidy_sats"], 1 if p["past"] else 0] for p in periods],
           "labels": {t["id"]: t["content"] for s in shots for t in s["text"]},
           "years": {str(h): round(year_at(h), 2) for h in [0, 210000, 420000, 630000, 840000, TIP] + [1050000 + 210000 * i for i in range(28)] + [LAST_SUBSIDY_BLOCK]}}
os.makedirs("film", exist_ok=True)
open("film/data.js", "w").write("// generated by tools/build.py — do not edit\nexport const DATA = " + json.dumps(data_js) + ";\n")
print("periods %d (past %d), facts %d, shots %d, events %d -> data/periods.csv facts.json shotspec.json film/data.js" % (
    len(periods), sum(1 for p in periods if p["past"]), len(facts), len(shots), len(events)))
