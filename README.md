# Alfred Workflows

## Water Tracker · 饮水记录

本地记录每日饮水量，查看目标剩余量和距上次饮水的时间。支持简体中文与 English。

A local-only daily water tracker with goal progress, time since the last drink,
and configurable interval hints. Supports Simplified Chinese and English.

- **安装 / Install:** 下载并双击 / Download and open `WaterTracker.alfredworkflow`.
- **要求 / Requires:** Alfred 5 + Powerpack, Python 3.9+.
- **配置 / Configure:** Configure Workflow → Language / 语言.
- **中文说明:** [WaterTracker/README.md](WaterTracker/README.md)
- **English guide:** [WaterTracker/README.en.md](WaterTracker/README.en.md)

源码和测试在 `WaterTracker` 中。仓库保留生成的安装包，方便直接下载；
个人配置、饮水数据库和缓存不纳入版本管理。

Source and tests live in `WaterTracker`. The generated package is tracked for
easy installation; personal preferences, water logs and caches are excluded.

## 构建与测试 / Build and test

```sh
cd WaterTracker
python3 build.py
python3 -m unittest discover -s tests -v
```
