#!/usr/bin/env python3
"""Build the Alfred metadata and importable package, with no local preferences."""
from pathlib import Path
import plistlib
import zipfile

ROOT = Path(__file__).resolve().parent
FILTER = "4800F1E7-FC26-4C26-859B-9947FE11B5BC"
ACTION = "15115856-A5E7-424F-8F6C-96B553DFE105"
NOTICE = "08DC5E69-E288-4149-B3EC-890C87AD6FEF"


def configuration(variable, label, default, description):
    return {
        "type": "textfield", "variable": variable, "label": label,
        "description": description,
        "config": {"default": default, "placeholder": default, "required": True, "trim": True},
    }


def build():
    metadata = {
        "bundleid": "local.kei.water-tracker", "name": "Water Tracker · 饮水记录",
        "description": "Daily water intake and interval hints / 每日饮水记录与间隔提示",
        "createdby": "Kei", "category": "Productivity", "version": "1.1.0",
        "disabled": False, "webaddress": "",
        "readme": (ROOT / "README.md").read_text() + "\n\n---\n\n" + (ROOT / "README.en.md").read_text(),
        "objects": [
            {"uid": FILTER, "type": "alfred.workflow.input.scriptfilter", "version": 3,
             "config": {
                 "keyword": "water", "title": "Water Tracker · 饮水记录",
                 "subtext": "Status / 状态 · add / 350 / undo",
                 "runningsubtext": "Loading / 正在读取…", "argumenttype": 1,
                 "argumenttreatemptyqueryasnil": False, "argumenttrimmode": 0,
                 "withspace": True, "alfredfiltersresults": False,
                 "alfredfiltersresultsmatchmode": 0,
                 "script": '/bin/bash ./run.sh filter "$1"', "scriptfile": "",
                 "type": 0, "scriptargtype": 1, "escaping": 0,
                 "queuedelaycustom": 1, "queuedelayimmediatelyinitially": True,
                 "queuedelaymode": 0, "queuemode": 1,
             }},
            {"uid": ACTION, "type": "alfred.workflow.action.script", "version": 2,
             "config": {"script": '/bin/bash ./run.sh action "$1"', "scriptfile": "",
                        "type": 0, "scriptargtype": 1, "escaping": 0, "concurrently": False}},
            {"uid": NOTICE, "type": "alfred.workflow.output.notification", "version": 1,
             "config": {"title": "Water Tracker · 饮水记录", "text": "{query}", "lastpathcomponent": False,
                        "removeextension": False, "onlyshowifquerypopulated": True}},
        ],
        "connections": {
            FILTER: [{"destinationuid": ACTION, "modifiers": 0, "modifiersubtext": "", "vitoclose": True}],
            ACTION: [{"destinationuid": NOTICE, "modifiers": 0, "modifiersubtext": "", "vitoclose": False}],
        },
        "uidata": {FILTER: {"xpos": 60, "ypos": 60}, ACTION: {"xpos": 330, "ypos": 60},
                   NOTICE: {"xpos": 600, "ypos": 60}},
        "userconfigurationconfig": [
            {"type": "popupbutton", "variable": "language", "label": "Language / 语言",
             "description": "Result and message language / 菜单和消息使用的语言",
             "config": {"default": "zh", "pairs": [["简体中文", "zh"], ["English", "en"]]}},
            configuration("cup_ml", "Cup size / 一杯的容量（ml）", "250",
                          "Amount per water add; integer 1–10000 / 每次记录一杯的毫升数，整数。"),
            configuration("goal_ml", "Daily goal / 每日目标（ml）", "2000",
                          "Integer 1–100000; default is an example / 整数；默认值仅为示例。"),
            configuration("interval_minutes", "Interval / 补水间隔（min）", "60",
                          "Integer 1–1440; lookup only, no background alerts / 整数；仅查询时提示，不后台推送。"),
        ],
        "variablesdontexport": [],
    }
    (ROOT / "info.plist").write_bytes(plistlib.dumps(metadata, sort_keys=False))
    output = ROOT / "dist" / "WaterTracker.alfredworkflow"
    output.parent.mkdir(parents=True, exist_ok=True)
    # Explicit allowlist keeps tests, caches, databases and personal settings out.
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in ("info.plist", "water.py", "strings.py", "run.sh", "README.md", "README.en.md"):
            archive.write(ROOT / name, name)
    print(output)


if __name__ == "__main__":
    build()
