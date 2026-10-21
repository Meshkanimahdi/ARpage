#!/usr/bin/env python3
"""Tehran clock helpers for the meshkani.pro publisher.

  tehran.py now                      current Tehran time (ISO)
  tehran.py slot prepare|publish     which slot this run serves, with deadlines (JSON)
  tehran.py wait-until HH:MM         block until that Tehran time today (max 9 minutes)
  tehran.py check-deadline SLOTKEY   exit 0 if still inside the publish window, 3 if late
  tehran.py reel prepare|publish     which daily story reel (09:00 or 15:00) this run serves (JSON)
"""
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

CONFIG = json.loads((Path(__file__).resolve().parent.parent / "config.json").read_text())
TZ = ZoneInfo(CONFIG["timezone"])
GRACE = timedelta(minutes=CONFIG["grace_minutes"])


def now():
    return datetime.now(TZ)


def at(day, hhmm):
    h, m = map(int, hhmm.split(":"))
    return datetime(day.year, day.month, day.day, h, m, tzinfo=TZ)


def slot_info(phase):
    """Pick the slot whose window contains now: from 120 minutes before the
    publish time until the end of the grace period."""
    t = now()
    for slot, s in CONFIG["slots"].items():
        publish = at(t, s["publish_at"])
        if publish - timedelta(minutes=120) <= t <= publish + GRACE:
            return {
                "phase": phase,
                "slot_key": f"{publish:%Y-%m-%d}|{slot}",
                "slot_file": f"slot_{publish:%Y-%m-%d}_{slot.replace(':', '')}.json",
                "date": f"{publish:%Y-%m-%d}",
                "slot": slot,
                "now_tehran": t.isoformat(timespec="seconds"),
                "prepare_start": at(t, s["prepare_start"]).isoformat(timespec="seconds"),
                "publish_at": publish.isoformat(timespec="seconds"),
                "deadline": (publish + GRACE).isoformat(timespec="seconds"),
                "minutes_to_publish": round((publish - t).total_seconds() / 60, 1),
                "minutes_to_deadline": round((publish + GRACE - t).total_seconds() / 60, 1),
            }
    return {"phase": phase, "slot_key": None, "now_tehran": t.isoformat(timespec="seconds"),
            "error": "No slot window is open now."}


def reel_info(phase):
    """Daily story reels at 09:00 and 15:00 (config reel.slots).
    prepare: 21:30-23:59 -> tomorrow 09:00; 00:00-08:30 -> today 09:00; 12:30-14:30 -> today 15:00.
    publish: the reel whose time is within 120 min before .. grace after now."""
    r, t = CONFIG["reel"], now()
    publish = None
    for slot, s in r["slots"].items():
        p_today = at(t, slot)
        w0, w1 = (at(t, x) for x in s["prepare_window"])
        if phase == "prepare":
            if w0 <= w1 and w0 <= t <= w1:
                publish = p_today
            elif w0 > w1:            # window crosses midnight: evening prepares tomorrow's reel
                if t >= w0:
                    publish = p_today + timedelta(days=1)
                elif t <= w1:
                    publish = p_today
        elif p_today - timedelta(minutes=120) <= t <= p_today + GRACE:
            publish = p_today
        if publish:
            break
    if publish is None:
        return {"phase": phase, "slot_key": None, "now_tehran": t.isoformat(timespec="seconds"),
                "error": "No reel window is open now."}
    hhmm = f"{publish:%H:%M}"
    return {
        "phase": phase, "kind": "reel",
        "slot_key": f"{publish:%Y-%m-%d}|{hhmm}",
        "slot_file": f"slot_{publish:%Y-%m-%d}_{hhmm.replace(':', '')}.json",
        "date": f"{publish:%Y-%m-%d}", "slot": hhmm,
        "other_reel_today": [f"slot_{publish:%Y-%m-%d}_{x.replace(':', '')}.json" for x in r["slots"] if x != hhmm],
        "now_tehran": t.isoformat(timespec="seconds"),
        "publish_at": publish.isoformat(timespec="seconds"),
        "deadline": (publish + GRACE).isoformat(timespec="seconds"),
        "minutes_to_publish": round((publish - t).total_seconds() / 60, 1),
    }


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "now":
        print(now().isoformat(timespec="seconds"))
        return 0
    if cmd == "slot":
        info = slot_info(argv[2] if len(argv) > 2 else "prepare")
        print(json.dumps(info, ensure_ascii=False, indent=1))
        return 0 if info.get("slot_key") else 1
    if cmd == "reel":
        info = reel_info(argv[2] if len(argv) > 2 else "prepare")
        print(json.dumps(info, ensure_ascii=False, indent=1))
        return 0 if info.get("slot_key") else 1
    if cmd == "wait-until":
        target = at(now(), argv[2])
        delay = (target - now()).total_seconds()
        if delay > 540:
            print(f"Refusing to wait {delay:.0f}s (>9 min); call again later.")
            return 4
        if delay > 0:
            time.sleep(delay)
        print(now().isoformat(timespec="seconds"))
        return 0
    if cmd == "check-deadline":
        day, slot = argv[2].split("|")
        publish = at(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=TZ), slot)
        late = now() > publish + GRACE
        print(json.dumps({"slot_key": argv[2], "now": now().isoformat(timespec="seconds"),
                          "deadline": (publish + GRACE).isoformat(timespec="seconds"),
                          "late": late}))
        return 3 if late else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
