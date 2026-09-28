# Water Tracker

English | [简体中文](README.md)

A local-only Alfred 5 workflow to log finished drinks, track daily intake and
show the time since your last drink. No network requests, uploads or background alerts.

## Install and configure

Requires **Alfred 5 + Powerpack** and **Python 3.9+**. No third-party Python libraries.

1. Download `WaterTracker.alfredworkflow` from the repository's **Releases** page
   and open it. If no release is available yet, build from source as described
   below; the package will be at `dist/WaterTracker.alfredworkflow`.
2. Confirm the import in Alfred, then select **English** under **Language / 语言**.
3. Set your cup size, daily goal and interval. Open Alfred and type `water`.

To change settings later: Alfred Preferences → Workflows → Water Tracker →
**Configure Workflow…**. The default language remains Simplified Chinese for
existing users. Missing or unsupported language values fall back to Chinese.

The launcher checks `/opt/homebrew/bin/python3`, `/usr/local/bin/python3` and
`/usr/bin/python3`. If Python is missing, install a current
[Python macOS package](https://www.python.org/downloads/macos/) and retry.
The workflow does not install dependencies or change your development environment.

The repository root is `WaterTracker` and directly contains the source and tests.
The parent `Alfred` folder is only a local organizational folder, not part of the
repository. Downloading source alone does not install the workflow; build and
import the package first.

## Commands

| Input | Result |
| --- | --- |
| `water` / `water status` | Today's total, remaining goal, entry count, time since last drink and interval hint |
| `water add` | Press Return to log one finished cup |
| `water 350` / `water add 350` | Press Return to log 350 ml |
| `water undo` | Press Return to remove today's last entry |
| `water settings` / `water help` | View current settings and usage |

Typing or browsing never adds a drink. Pressing Return on the first status row
only displays a notification. Choose the log entry to save a drink; its finish
time is the time you confirm it. Amounts must be whole ml from 1 to 10000.
This input range is not a recommendation for how much to drink.

| Setting | Default | Meaning |
| --- | --- | --- |
| Language | Simplified Chinese | Select English; records, commands and units do not change |
| Cup size | 250 ml | Amount for future one-cup entries; old amounts stay unchanged |
| Daily goal | 2000 ml | Used to calculate the remaining amount |
| Interval | 60 minutes | Time after the last recorded finished drink before a hint appears |

Defaults are editable examples, not personal medical advice. If your goal is
not reached and the interval has elapsed, the workflow suggests considering
some water. Otherwise it shows the remaining interval. Without a previous entry
it does not guess the last-drink time. After reaching the goal, interval hints
pause but logging still works. It does not diagnose dehydration or suggest
ignoring thirst. Hints appear only during lookup; there are no scheduled
notifications, background processes or global hotkeys.

## Development

From the repository root, build the metadata/package and then run tests:

```sh
python3 build.py
python3 -m unittest discover -s tests -v
```

Tests use temporary directories, never your real drinking records. The builder
creates `info.plist` and `dist/WaterTracker.alfredworkflow` inside the repository,
without writing the package into its parent folder.
Personal preferences, databases, tests and caches are excluded from the package.

### Release artifacts

- `info.plist` remains tracked because Alfred needs this runtime metadata. Commit
  any generated changes together with the corresponding source changes.
- `dist/` and all `.alfredworkflow` packages are ignored, not committed with source.
- Upload the built and tested `dist/WaterTracker.alfredworkflow` as an attachment
  to the matching version's **Release**.
- Match the release tag to the workflow version in `build.py`, for example
  version `1.1.0` uses tag `v1.1.0`.
- Pushing source and tags does not upload the package automatically. No automated
  publishing workflow is configured in this repository yet.

To test manually without changing real records:

```sh
export alfred_workflow_data="$(mktemp -d)"
export language=en
/bin/bash ./run.sh filter ''
/bin/bash ./run.sh action '{"op":"add","amount":250}'
/bin/bash ./run.sh filter status
```

## Alfred references

- [Script Filter JSON](https://www.alfredapp.com/help/workflows/inputs/script-filter/json/)
- [Environment variables and data directories](https://www.alfredapp.com/help/workflows/script-environment-variables/)
- [Workflow configuration](https://www.alfredapp.com/help/workflows/workflow-configuration/)
