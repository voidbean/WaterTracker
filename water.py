#!/usr/bin/env python3
"""Local-only Alfred water log. Python 3.9+, standard library only."""

import json
import math
import os
from pathlib import Path
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from functools import partial

from strings import UserError, language_from_env, tr

BUNDLE_ID = "local.kei.water-tracker"


def positive_int(value, label, maximum):
    text = str(value).strip()
    if not re.fullmatch(r"[0-9]{1,6}", text) or not 1 <= int(text) <= maximum:
        raise UserError("integer_required", label=label, maximum=maximum)
    return int(text)


@dataclass(frozen=True)
class Settings:
    cup: int = 250
    goal: int = 2000
    interval: int = 60
    language: str = "zh"

    @classmethod
    def from_env(cls):
        return cls(
            positive_int(os.environ.get("cup_ml", "250"), "cup_label", 10000),
            positive_int(os.environ.get("goal_ml", "2000"), "goal_label", 100000),
            positive_int(os.environ.get("interval_minutes", "60"), "interval_label", 1440),
            language_from_env(os.environ),
        )


class Store:
    def __init__(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(directory / "water.sqlite3", timeout=5)
        self.db.row_factory = sqlite3.Row
        with self.db:
            self.db.execute("""CREATE TABLE IF NOT EXISTS drinks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day TEXT NOT NULL,
                finished_at REAL NOT NULL,
                amount INTEGER NOT NULL CHECK(amount > 0 AND amount <= 10000)
            )""")
            self.db.execute("CREATE INDEX IF NOT EXISTS drinks_day ON drinks(day)")

    def close(self):
        self.db.close()

    def add(self, amount, now):
        amount = positive_int(amount, "amount_label", 10000)
        with self.db:
            self.db.execute(
                "INSERT INTO drinks(day, finished_at, amount) VALUES (?, ?, ?)",
                (now.date().isoformat(), now.timestamp(), amount),
            )

    def undo(self, event_id, day, now):
        # Bind undo to the displayed event and local day; stale menus cannot delete
        # a newly added drink or yesterday's record after crossing midnight.
        if day != now.date().isoformat():
            raise UserError("day_changed")
        with self.db:
            cursor = self.db.execute(
                """DELETE FROM drinks WHERE id = ? AND day = ?
                AND id = (SELECT MAX(id) FROM drinks WHERE day = ?)""",
                (event_id, day, day),
            )
            if cursor.rowcount != 1:
                raise UserError("record_changed")

    def snapshot(self, now):
        # Keep totals, last drink and undo target in one read transaction.
        self.db.execute("BEGIN")
        try:
            today = [dict(row) for row in self.db.execute(
                "SELECT * FROM drinks WHERE day = ? ORDER BY id",
                (now.date().isoformat(),),
            )]
            last = self.db.execute("SELECT * FROM drinks ORDER BY id DESC LIMIT 1").fetchone()
            return today, dict(last) if last else None
        finally:
            self.db.rollback()


def elapsed_text(seconds, language="zh"):
    minutes = int(max(0, seconds) // 60)
    if minutes == 0:
        return tr("under_minute", language)
    days, minutes = divmod(minutes, 1440)
    hours, minutes = divmod(minutes, 60)
    return " ".join(tr(unit, language, n=n) for n, unit in
                    ((days, "days"), (hours, "hours"), (minutes, "minutes")) if n)


def summary(today, last, settings, now):
    t = partial(tr, language=settings.language)
    total = sum(row["amount"] for row in today)
    remaining = max(0, settings.goal - total)
    progress = t("progress", total=total, goal=settings.goal, count=len(today))
    balance = (t("remaining", remaining=remaining, cups=remaining / settings.cup)
               if remaining else t("completed", extra=total - settings.goal))
    if last is None:
        since = t("no_records")
    elif last["finished_at"] > now.timestamp():
        since = t("future_record")
    else:
        since = t("since", elapsed=elapsed_text(now.timestamp() - last["finished_at"], settings.language))

    if remaining == 0:
        prompt = t("goal_reached")
    elif last is None:
        prompt = t("no_time")
    elif last["finished_at"] > now.timestamp():
        prompt = t("clock_error")
    else:
        wait = settings.interval * 60 - (now.timestamp() - last["finished_at"])
        prompt = t("due") if wait <= 0 else t("not_due", minutes=math.ceil(wait / 60))
    return progress, balance, since, prompt


def item(title, subtitle="", action=None, autocomplete=None):
    result = {"title": title, "subtitle": subtitle, "valid": action is not None}
    if action is not None:
        result["arg"] = json.dumps(action, ensure_ascii=False)
    if autocomplete is not None:
        result["autocomplete"] = autocomplete
    return result


def add_item(amount, language="zh"):
    return item(tr("add", language, amount=amount), tr("add_hint", language),
                {"op": "add", "amount": amount})


def undo_item(today, language="zh"):
    if not today:
        return item(tr("nothing_to_undo", language))
    last = today[-1]
    return item(tr("undo", language, amount=last["amount"]), tr("undo_hint", language),
                {"op": "undo", "id": last["id"], "day": last["day"]})


def render(query, store, settings, now):
    t = partial(tr, language=settings.language)
    today, last = store.snapshot(now)
    progress, balance, since, prompt = summary(today, last, settings, now)
    query = query.strip().lower()
    if query in ("", "status"):
        rows = [
            item(progress, balance, {"op": "status"}),
            item(since, prompt),
            add_item(settings.cup, settings.language),
            undo_item(today, settings.language),
            item(t("settings"), t("settings_hint"), autocomplete="settings"),
        ]
    elif query == "undo":
        rows = [undo_item(today, settings.language)]
    elif query in ("settings", "help"):
        rows = [
            item(t("settings_values", cup=settings.cup, goal=settings.goal),
                 t("settings_edit", interval=settings.interval)),
            item(t("usage"), t("usage_more")),
            item(t("local_day"), t("disclaimer")),
        ]
    elif query == "add":
        rows = [add_item(settings.cup, settings.language)]
    else:
        amount_text = query[4:].strip() if query.startswith("add ") else query
        if re.fullmatch(r"[0-9]+", amount_text):
            rows = [add_item(positive_int(amount_text, "amount_label", 10000), settings.language)]
        else:
            commands = {"add": t("command_add"), "status": t("command_status"),
                        "undo": t("command_undo"), "settings": t("settings"), "help": t("command_help")}
            rows = [item(title, t("autocomplete", command=cmd), autocomplete=cmd)
                    for cmd, title in commands.items() if cmd.startswith(query)]
            if not rows:
                rows = [item(t("unknown_input"), t("valid_commands"))]
    return {"items": rows, "rerun": 5}


def perform(payload, store, settings, now):
    t = partial(tr, language=settings.language)
    try:
        action = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise UserError("invalid_action") from exc
    if not isinstance(action, dict):
        raise UserError("invalid_action")
    op = action.get("op")
    if op == "add":
        amount = positive_int(action.get("amount"), "amount_label", 10000)
        store.add(amount, now)
        prefix = t("added", amount=amount)
    elif op == "undo":
        if type(action.get("id")) is not int or not isinstance(action.get("day"), str):
            raise UserError("invalid_undo")
        store.undo(action["id"], action["day"], now)
        prefix = t("undone")
    elif op == "status":
        prefix = ""
    else:
        raise UserError("unknown_action")
    today, last = store.snapshot(now)
    return prefix + t("separator").join(summary(today, last, settings, now))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "filter"
    query = sys.argv[2] if len(sys.argv) > 2 else ""
    store = None
    language = language_from_env(os.environ)
    try:
        if mode not in ("filter", "action"):
            raise UserError("invalid_mode")
        settings = Settings.from_env()
        directory = os.environ.get("alfred_workflow_data") or str(
            Path.home() / "Library/Application Support/Alfred/Workflow Data" / BUNDLE_ID)
        store = Store(directory)
        now = datetime.now().astimezone()
        result = render(query, store, settings, now) if mode == "filter" else perform(query, store, settings, now)
        print(json.dumps(result, ensure_ascii=False) if mode == "filter" else result)
        return 0
    except (ValueError, OSError, sqlite3.Error) as exc:
        detail = exc.localized(language) if isinstance(exc, UserError) else str(exc)
        message = tr("failed", language, detail=detail)
        if mode == "filter":
            print(json.dumps({"items": [item(message, tr("error_hint", language))]}, ensure_ascii=False))
        else:
            print(message)
        print(message, file=sys.stderr)
        return 1
    finally:
        if store is not None:
            store.close()


if __name__ == "__main__":
    sys.exit(main())
