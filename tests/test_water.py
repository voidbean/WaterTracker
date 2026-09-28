import concurrent.futures
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import plistlib
import shutil
import sqlite3
from string import Formatter
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from water import Settings, Store, elapsed_text, perform, positive_int, render, summary
from strings import MESSAGES, UserError, language_from_env


class WaterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.now = datetime(2026, 9, 22, 10, 0, tzinfo=timezone(timedelta(hours=8)))
        self.settings = Settings()

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def state(self, now=None, settings=None):
        now = now or self.now
        return summary(*self.store.snapshot(now), settings or self.settings, now)

    def test_empty_state_does_not_invent_time(self):
        self.assertIn("今日 0 / 2000", self.state()[0])
        self.assertIn("2000 ml", self.state()[1])
        self.assertEqual(self.state()[2], "尚无饮水记录")
        self.assertIn("暂无时间依据", self.state()[3])

    def test_add_and_persistence(self):
        perform('{"op":"add","amount":350}', self.store, self.settings, self.now)
        other = Store(self.temp.name)
        try:
            self.assertEqual(other.snapshot(self.now)[0][0]["amount"], 350)
        finally:
            other.close()
        self.assertIn("1650 ml", self.state()[1])

    def test_preview_and_status_are_read_only(self):
        for query in ("", "status", "add", "350", "add 350", "settings", "undo", "a"):
            render(query, self.store, self.settings, self.now)
        perform('{"op":"status"}', self.store, self.settings, self.now)
        self.assertEqual(self.store.snapshot(self.now), ([], None))

    def test_default_action_is_status_not_add(self):
        rows = render("", self.store, self.settings, self.now)["items"]
        self.assertEqual(json.loads(rows[0]["arg"]), {"op": "status"})
        self.assertFalse(rows[1]["valid"])
        self.assertEqual(json.loads(rows[2]["arg"]), {"op": "add", "amount": 250})

    def test_midnight_resets_today_but_preserves_last(self):
        last_night = self.now.replace(hour=23, minute=50) - timedelta(days=1)
        self.store.add(250, last_night)
        self.assertIn("今日 0", self.state()[0])
        self.assertIn("10 小时 10 分钟", self.state()[2])
        self.assertIn("已到", self.state()[3])
        self.store.add(300, self.now)
        self.assertIn("今日 300", self.state()[0])
        self.assertEqual(len(self.store.snapshot(last_night)[0]), 1)

    def test_exact_interval_boundary(self):
        self.store.add(250, self.now)
        self.assertIn("1 分钟后", self.state(self.now + timedelta(minutes=59, seconds=59))[3])
        self.assertIn("已到", self.state(self.now + timedelta(minutes=60))[3])

    def test_goal_and_over_goal_never_negative(self):
        self.store.add(2000, self.now)
        self.assertIn("目标已完成", self.state()[1])
        self.assertIn("不再", self.state(self.now + timedelta(hours=2))[3])
        self.store.add(250, self.now)
        self.assertIn("超出 250", self.state()[1])

    def test_settings_changes_never_rescale_history(self):
        self.store.add(250, self.now)
        state = self.state(settings=Settings(500, 1500, 30))
        self.assertIn("今日 250 / 1500", state[0])
        self.assertIn("2.5 杯", state[1])

    def test_undo_restores_previous_timestamp(self):
        self.store.add(250, self.now - timedelta(minutes=30))
        self.store.add(350, self.now)
        action = render("undo", self.store, self.settings, self.now)["items"][0]["arg"]
        perform(action, self.store, self.settings, self.now)
        self.assertIn("今日 250", self.state()[0])
        self.assertIn("30 分钟", self.state()[2])
        with self.assertRaises(ValueError):
            perform(action, self.store, self.settings, self.now)

    def test_undo_only_drink_restores_empty_state(self):
        self.store.add(250, self.now)
        action = render("undo", self.store, self.settings, self.now)["items"][0]["arg"]
        perform(action, self.store, self.settings, self.now)
        self.assertEqual(self.store.snapshot(self.now), ([], None))

    def test_stale_undo_cannot_remove_new_drink(self):
        self.store.add(250, self.now)
        action = render("undo", self.store, self.settings, self.now)["items"][0]["arg"]
        self.store.add(350, self.now)
        with self.assertRaises(ValueError):
            perform(action, self.store, self.settings, self.now)
        self.assertIn("今日 600", self.state()[0])

    def test_midnight_undo_rejected(self):
        self.store.add(250, self.now)
        action = render("undo", self.store, self.settings, self.now)["items"][0]["arg"]
        with self.assertRaises(ValueError):
            perform(action, self.store, self.settings, self.now + timedelta(days=1))
        self.assertIn("今日 250", self.state()[0])

    def test_future_timestamp_is_not_a_hydration_instruction(self):
        self.store.add(250, self.now + timedelta(hours=1))
        self.assertIn("检查系统时钟", self.state()[2])
        self.assertIn("暂不判断", self.state()[3])

    def test_timezone_changes_preserve_recorded_day(self):
        moment = self.now.replace(hour=0, minute=30)
        self.store.add(250, moment)
        utc = moment.astimezone(timezone.utc)
        self.assertEqual(self.store.snapshot(utc)[0], [])
        self.assertIn("不足 1 分钟", self.state(utc)[2])

    def test_elapsed_format(self):
        for seconds, expected in [(0, "不足 1 分钟"), (60, "1 分钟"), (3600, "1 小时"),
                                  (90060, "1 天 1 小时 1 分钟")]:
            self.assertEqual(elapsed_text(seconds), expected)

    def test_invalid_amounts_and_actions(self):
        for amount in (0, -1, 1.5, True, None, "nan", "inf", "10001", "1" * 5000):
            with self.subTest(amount=str(amount)[:30]), self.assertRaises(ValueError):
                positive_int(amount, "amount_label", 10000)
        for payload in ('[]', 'null', '{}', '{"op":"oops"}', '{"op":"add"}',
                        '{"op":"undo","id":true,"day":"2026-09-22"}', 'not json'):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                perform(payload, self.store, self.settings, self.now)

    def test_settings_validation(self):
        with patch.dict(os.environ, {"cup_ml": "300", "goal_ml": "1800", "interval_minutes": "45", "language": "zh"}):
            self.assertEqual(Settings.from_env(), Settings(300, 1800, 45))
        for key, value in [("cup_ml", "0"), ("goal_ml", ""), ("interval_minutes", "1441")]:
            with patch.dict(os.environ, {key: value}), self.assertRaises(ValueError):
                Settings.from_env()

    def test_concurrent_adds_preserve_all_events(self):
        def add(_):
            store = Store(self.temp.name)
            try:
                store.add(100, self.now)
            finally:
                store.close()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(add, range(32)))
        self.assertEqual(len(self.store.snapshot(self.now)[0]), 32)
        self.assertIn("今日 3200", self.state()[0])

    def test_failed_transaction_rolls_back(self):
        with self.assertRaises(sqlite3.IntegrityError), self.store.db:
            self.store.db.execute("INSERT INTO drinks(day, finished_at, amount) VALUES ('2026-09-22', 1, 250)")
            self.store.db.execute("INSERT INTO drinks(day, finished_at, amount) VALUES ('2026-09-22', 1, 0)")
        self.assertEqual(self.store.snapshot(self.now), ([], None))

    def test_unknown_input_is_not_executed(self):
        rows = render('$(touch /tmp/not-a-water-command)', self.store, self.settings, self.now)["items"]
        self.assertFalse(rows[0]["valid"])
        self.assertEqual(self.store.snapshot(self.now), ([], None))


class IntegrationTests(unittest.TestCase):
    def test_builder_keeps_artifacts_inside_repository(self):
        with tempfile.TemporaryDirectory(prefix="water clean build ") as directory:
            checkout = Path(directory) / "WaterTracker"
            checkout.mkdir()
            runtime_files = {"water.py", "strings.py", "run.sh", "README.md", "README.en.md"}
            for name in runtime_files | {"build.py"}:
                shutil.copy2(ROOT / name, checkout / name)
            result = subprocess.run([sys.executable, str(checkout / "build.py")],
                                    cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            package = checkout / "dist" / "WaterTracker.alfredworkflow"
            self.assertEqual(Path(result.stdout.strip()).resolve(), package.resolve())
            self.assertEqual(set(Path(directory).iterdir()), {checkout})
            self.assertTrue((checkout / "info.plist").is_file())
            with zipfile.ZipFile(package) as archive:
                self.assertEqual(set(archive.namelist()), runtime_files | {"info.plist"})
                self.assertIsNone(archive.testzip())

    def cli(self, directory, mode, query, **env):
        environment = dict(os.environ, alfred_workflow_data=str(directory), cup_ml="250",
                           goal_ml="2000", interval_minutes="60", language="zh", PYTHONDONTWRITEBYTECODE="1")
        environment.update(env)
        return subprocess.run(["/bin/bash", str(ROOT / "run.sh"), mode, query],
                              env=environment, capture_output=True, text=True)

    def test_launcher_under_alfred_path_and_action_roundtrip(self):
        with tempfile.TemporaryDirectory(prefix="water test ") as directory:
            preview = self.cli(directory, "filter", "350", PATH="/usr/bin:/bin")
            self.assertEqual(preview.returncode, 0, preview.stderr)
            action = json.loads(preview.stdout)["items"][0]["arg"]
            added = self.cli(directory, "action", action, PATH="/usr/bin:/bin")
            self.assertEqual(added.returncode, 0, added.stderr)
            self.assertIn("已记录 350 ml", added.stdout)
            status = self.cli(directory, "filter", "")
            self.assertIn("今日 350", json.loads(status.stdout)["items"][0]["title"])

    def test_bad_config_yields_alfred_json(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.cli(directory, "filter", "", cup_ml="zero")
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)["items"][0]["valid"])
            self.assertFalse((Path(directory) / "water.sqlite3").exists())

    def test_corrupt_data_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "water.sqlite3"
            original = b"not a sqlite database"
            path.write_bytes(original)
            result = self.cli(directory, "filter", "")
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)["items"][0]["valid"])
            self.assertEqual(path.read_bytes(), original)

    def test_unwritable_data_location_returns_error(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "not-a-directory"
            file.write_text("keep")
            result = self.cli(file, "filter", "")
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)["items"][0]["valid"])
            self.assertEqual(file.read_text(), "keep")

    def test_package_metadata_and_exact_contents(self):
        metadata = plistlib.loads((ROOT / "info.plist").read_bytes())
        self.assertEqual(metadata["bundleid"], "local.kei.water-tracker")
        objects = metadata["objects"]
        self.assertEqual(objects[0]["config"]["argumenttype"], 1)
        self.assertFalse(objects[0]["config"]["alfredfiltersresults"])
        ids = {obj["uid"] for obj in objects}
        for source, connections in metadata["connections"].items():
            self.assertIn(source, ids)
            for connection in connections:
                self.assertIn(connection["destinationuid"], ids)
        for option in metadata["userconfigurationconfig"]:
            self.assertIn(option["variable"], ("cup_ml", "goal_ml", "interval_minutes", "language"))
        language_option = next(c for c in metadata["userconfigurationconfig"] if c["variable"] == "language")
        self.assertEqual(language_option["type"], "popupbutton")
        self.assertEqual(language_option["config"], {"default": "zh", "pairs": [["简体中文", "zh"], ["English", "en"]]})
        with zipfile.ZipFile(ROOT / "dist" / "WaterTracker.alfredworkflow") as archive:
            self.assertEqual(set(archive.namelist()), {"info.plist", "water.py", "strings.py", "run.sh", "README.md", "README.en.md"})
            self.assertIsNone(archive.testzip())
            for name in archive.namelist():
                self.assertEqual(archive.read(name), (ROOT / name).read_bytes())

    def test_switch_language_with_existing_records(self):
        with tempfile.TemporaryDirectory() as directory:
            added = self.cli(directory, "action", '{"op":"add","amount":350}')
            self.assertEqual(added.returncode, 0, added.stderr)
            english = self.cli(directory, "filter", "", language="en")
            self.assertEqual(english.returncode, 0, english.stderr)
            self.assertIn("Today: 350 / 2000", json.loads(english.stdout)["items"][0]["title"])
            self.assertNotRegex(english.stdout, r"[\u4e00-\u9fff]")
            undo = self.cli(directory, "filter", "undo", language="en")
            result = self.cli(directory, "action", json.loads(undo.stdout)["items"][0]["arg"], language="en")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Entry undone.", result.stdout)
            self.assertNotRegex(result.stdout, r"[\u4e00-\u9fff]")
            chinese = self.cli(directory, "filter", "")
            self.assertIn("今日 0 / 2000", json.loads(chinese.stdout)["items"][0]["title"])

    def test_english_config_input_and_action_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            for overrides, mode, query, message in [
                ({"cup_ml": "0"}, "filter", "", "Cup size (ml)"),
                ({"goal_ml": "oops"}, "filter", "", "Daily goal (ml)"),
                ({"interval_minutes": "-1"}, "filter", "", "Interval (minutes)"),
                ({}, "filter", "0", "Drink amount (ml)"),
                ({}, "action", "not json", "Invalid action"),
                ({}, "action", '{"op":"add","amount":0}', "Drink amount (ml)"),
                ({}, "action", '{"op":"undo","id":1,"day":"1900-01-01"}', "date has changed"),
                ({}, "action", '{"op":"undo","id":true}', "Invalid undo action"),
                ({}, "action", '{"op":"unknown"}', "Unknown action"),
                ({}, "invalid-mode", "", "Mode must be filter or action"),
            ]:
                with self.subTest(overrides=overrides, mode=mode, query=query):
                    result = self.cli(directory, mode, query, language="en", **overrides)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn(message, result.stdout)
                    self.assertNotRegex(result.stdout, r"[\u4e00-\u9fff]")
                    if mode == "filter":
                        self.assertFalse(json.loads(result.stdout)["items"][0]["valid"])

    def test_english_database_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "water.sqlite3"
            path.write_bytes(b"not a database")
            result = self.cli(directory, "filter", "", language="en")
            self.assertEqual(result.returncode, 1)
            self.assertIn("Water tracker could not complete", result.stdout)
            self.assertNotRegex(result.stdout, r"[\u4e00-\u9fff]")
            self.assertEqual(path.read_bytes(), b"not a database")

    def test_extracted_package_in_both_languages(self):
        with tempfile.TemporaryDirectory(prefix="water package ") as directory:
            cwd = Path(directory) / "workflow"
            with zipfile.ZipFile(ROOT / "dist" / "WaterTracker.alfredworkflow") as archive:
                archive.extractall(cwd)
            metadata = plistlib.loads((cwd / "info.plist").read_bytes())
            for lang in ("zh", "en"):
                env = dict(os.environ, PATH="/usr/bin:/bin", language=lang, cup_ml="300",
                           goal_ml="1800", interval_minutes="45",
                           alfred_workflow_data=str(Path(directory) / lang))
                def run(index, argument):
                    result = subprocess.run(
                        ["/bin/bash", "-c", metadata["objects"][index]["config"]["script"], "alfred", argument],
                        cwd=cwd, env=env, text=True, capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    return result.stdout
                action = json.loads(run(0, "add"))["items"][0]["arg"]
                self.assertEqual(json.loads(action)["amount"], 300)
                self.assertIn("300 / 1800", run(1, action))
                action = json.loads(run(0, "undo"))["items"][0]["arg"]
                self.assertIn("0 / 1800", run(1, action))

    def test_missing_python_messages_without_removing_real_python(self):
        # Run the launcher's actual no-runtime branch without touching installed runtimes.
        branch = (ROOT / "run.sh").read_text().split('selected_language=', 1)[1]
        script = 'set -eu\nselected_language=' + branch
        for lang, expected in (("zh", "需要 Python"), ("en", "Python 3.9 or newer"), (" EN ", "Python 3.9 or newer")):
            for mode in ("filter", "action"):
                result = subprocess.run(["/bin/bash", "-c", script, "launcher", mode],
                                        env=dict(os.environ, language=lang), capture_output=True, text=True)
                self.assertEqual(result.returncode, 1)
                self.assertIn(expected, result.stdout)
                if mode == "filter":
                    self.assertFalse(json.loads(result.stdout)["items"][0]["valid"])


class LanguageTests(unittest.TestCase):
    def test_catalog_keys_and_placeholders_match(self):
        self.assertEqual(MESSAGES["zh"].keys(), MESSAGES["en"].keys())
        def placeholders(text):
            return {(name, spec, conversion) for _, name, spec, conversion in Formatter().parse(text)
                    if name is not None}
        for key in MESSAGES["zh"]:
            with self.subTest(key=key):
                self.assertEqual(placeholders(MESSAGES["zh"][key]), placeholders(MESSAGES["en"][key]))
                self.assertTrue(MESSAGES["en"][key])
                self.assertNotRegex(MESSAGES["en"][key], r"[\u4e00-\u9fff]")

    def test_language_defaults_and_normalization(self):
        for value, expected in [(None, "zh"), ("", "zh"), ("fr", "zh"), ("zh", "zh"),
                                ("en", "en"), (" EN ", "en")]:
            self.assertEqual(language_from_env({} if value is None else {"language": value}), expected)
        with patch.dict(os.environ, {"language": "en", "cup_ml": "250", "goal_ml": "2000", "interval_minutes": "60"}):
            self.assertEqual(Settings.from_env(), Settings(language="en"))

    def test_english_elapsed_units(self):
        for seconds, expected in [(0, "less than 1 min"), (60, "1 min"), (120, "2 min"),
                                  (3600, "1 h"), (90060, "1 d 1 h 1 min")]:
            self.assertEqual(elapsed_text(seconds, "en"), expected)

    def test_all_english_menu_paths_and_payload_parity(self):
        now = datetime(2026, 9, 28, 12, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            try:
                for populated in (False, True):
                    if populated:
                        store.add(250, now)
                    for query in ("", "status", "add", "350", "add 350", "undo", "settings", "help",
                                  "a", "s", "u", "h", "unknown"):
                        with self.subTest(populated=populated, query=query):
                            english = render(query, store, Settings(language="en"), now)
                            chinese = render(query, store, Settings(), now)
                            self.assertNotRegex(json.dumps(english, ensure_ascii=False), r"[\u4e00-\u9fff]")
                            self.assertEqual(len(english["items"]), len(chinese["items"]))
                            for en, zh in zip(english["items"], chinese["items"]):
                                for key in ("valid", "arg", "autocomplete"):
                                    self.assertEqual(en.get(key), zh.get(key))
            finally:
                store.close()

    def test_english_summary_boundaries(self):
        now = datetime(2026, 9, 28, 12, tzinfo=timezone.utc)
        settings = Settings(language="en")
        event = {"amount": 250, "finished_at": now.timestamp()}
        self.assertIn("No drinks recorded", summary([], None, settings, now)[2])
        self.assertIn("Next hint in about 1 min", summary([event], event, settings, now + timedelta(seconds=3599))[3])
        self.assertIn("interval has elapsed", summary([event], event, settings, now + timedelta(hours=1))[3])
        future = summary([event], event, settings, now - timedelta(hours=1))
        self.assertIn("future", future[2])
        self.assertIn("Clock mismatch", future[3])
        complete = summary([dict(event, amount=2250)], event, settings, now)
        self.assertIn("250 ml above goal", complete[1])
        self.assertIn("hints are paused", complete[3])

    def test_domain_error_can_be_rendered_in_either_language(self):
        error = UserError("integer_required", label="amount_label", maximum=10000)
        self.assertIn("本次饮水量", error.localized("zh"))
        self.assertIn("Drink amount", error.localized("en"))
        self.assertIn("record changed", UserError("record_changed").localized("en"))


if __name__ == "__main__":
    unittest.main()
