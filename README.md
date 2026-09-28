# Water Tracker · 饮水记录

[English](README.en.md) | 简体中文

本地运行的 Alfred 5 工作流：记录饮用完毕的水量，按天统计，显示距离上次喝完多久。
不联网、不上传数据、不创建后台提醒任务。

## 安装

需要 **Alfred 5 + Powerpack** 和 **Python 3.9 或更新版本**，不需要安装 Python 第三方库。

1. 从仓库的 **Releases** 页面下载 `WaterTracker.alfredworkflow`，双击并在 Alfred 中确认导入。
   若尚未发布 Release，可按下文从源码构建，安装包位于 `dist/WaterTracker.alfredworkflow`。
2. 在导入配置页选择语言，设置杯容量、每日目标和补水间隔。
3. 呼出 Alfred，输入 `water`。

仓库根目录就是 `WaterTracker`，直接包含源码与测试；外层 `Alfred` 仅用于本地分类，不属于仓库。
下载源码不会自动启用工作流，必须先构建并导入安装包。
也可以通过 Alfred 工作流右键菜单的 Open in Finder 找到安装目录，将安装包内的文件复制到该目录。

启动脚本依次检查 `/opt/homebrew/bin/python3`、`/usr/local/bin/python3`、`/usr/bin/python3`。
若提示 Python 缺失，可以安装 [Python 官方 macOS 安装包](https://www.python.org/downloads/macos/)
后重新运行。不会自动下载依赖或修改你的开发环境。

## 用法

| 输入 | 效果 |
| --- | --- |
| `water` / `water status` | 今日总量、目标剩余量、饮水次数、距上次喝完的时间、补水间隔提示 |
| `water add` | 回车记录喝完一杯，以配置的杯容量计量 |
| `water 350` / `water add 350` | 回车记录喝完 350 ml |
| `water undo` | 回车撤销今天最后一笔，重新计算总量和上次饮水时间 |
| `water settings` / `water help` | 查看当前配置和使用说明 |

仅输入或浏览不会新增饮水记录。`water` 首行回车只显示状态通知；选择“喝完了，记录…”才会新增。
输入 `water add` 后也必须按回车确认。记录时间为确认时刻，不是开始喝水的时间。
饮水量只接受整数 ml，单笔范围为 1–10000；范围是输入保护，不是饮水建议。

配置入口：Alfred Preferences → Workflows → Water Tracker → **Configure Workflow…**。

| 配置 | 初始值 | 含义 |
| --- | --- | --- |
| Language / 语言 | 简体中文 | 可选择 English；只影响显示，不影响记录、命令或计量单位 |
| 一杯的容量 | 250 ml | 影响之后的一杯记录和剩余杯数换算；不改变历史毫升数 |
| 每日饮水目标 | 2000 ml | 按此目标计算当日剩余量，可随时修改 |
| 补水提示间隔 | 60 分钟 | 从最近一次饮用完毕记录起算 |

这些初始值只是可修改的示例，并非对个人的医疗建议。
未达目标且达到设定间隔时显示“可以考虑喝水了”；未到间隔时显示倒计时。
无记录时不猜测上次喝水时间；达到目标后停止间隔提示，但仍允许记录。
本工作流不判断身体是否缺水，也不会因为未到间隔就建议你忍渴。
提示仅在查询时出现，没有定时通知、后台程序或全局热键。

### 中英双语与升级

- 在 **Configure Workflow… → Language / 语言** 中切换简体中文或 English，下次查询即生效。
- 查询结果、时间描述、通知正文、帮助和应用错误提示随语言切换；系统错误的底层诊断保留原文。
- 配置页标签、加载占位文案和固定通知标题采用中英对照，不会随选择动态改变。
- `water`、`add`、`undo` 等命令和 ml 单位不变；语言缺失或不支持时回退到中文。
- 重新导入新版安装包更新工作流。沿用原 bundle ID 和数据库格式，无需迁移饮水记录。
- 所有运行时翻译集中在 `strings.py`，没有额外依赖；测试检查两种语言的键和格式占位符一致。

## 数据与日期边界

- 使用 Alfred 提供的 `alfred_workflow_data` 目录，数据库文件名为 `water.sqlite3`。
- 通常位置：`~/Library/Application Support/Alfred/Workflow Data/local.kei.water-tracker/water.sqlite3`。
- 每笔保存实际 ml、时间戳和记录时的本地日期；午夜后今日统计自然归零，历史不会删除。
- “距上次喝完”可跨天计算；昨天的记录仍是最近一次时会继续显示其间隔。
- 若切换系统时区，旧记录保留原记录日期，不重新分组；之后的记录按新本地日期归档。
- 撤销仅作用于菜单显示的今天最后一笔。菜单过期、已有新记录或跨午夜时会拒绝撤销，避免误删。
- SQLite 事务处理并发与异常中断；数据库不可写或损坏时显示错误，不会用空记录覆盖原文件。
- 退出 Alfred 后可复制整个数据目录备份。重新导入工作流不包含或覆盖个人记录。
- 本地记录不会加密；遵循 macOS 用户目录权限。不提供云同步或历史数据浏览界面。

## 开发验证与重新打包

在仓库根目录运行（命令中的 `python3` 需要对应 Python 3.9+）：

```sh
python3 build.py
python3 -m unittest discover -s tests -v
```

测试使用临时目录，不写入真实饮水记录。`build.py` 生成 `info.plist` 和
`dist/WaterTracker.alfredworkflow`；不再向仓库外写入安装包。
仅打包运行必需的文件，不打包本机配置、数据库、测试或缓存。

### 发布产物

- `info.plist` 是 Alfred 运行必需的元数据，继续纳入版本管理；构建后如有变化需和源码一起提交。
- `dist/` 和所有 `.alfredworkflow` 安装包均已忽略，不随源码提交。
- 发布时，将经过构建和测试的 `dist/WaterTracker.alfredworkflow` 上传为对应版本的 **Release 附件**。
- 发布标签应与 `build.py` 中的工作流版本一致，例如版本 `1.1.0` 对应标签 `v1.1.0`。
- Git 推送源码与标签不会自动上传安装包；本仓库目前没有配置自动发布。

终端调试时可用临时数据目录隔离真实记录：

```sh
export alfred_workflow_data="$(mktemp -d)"
/bin/bash ./run.sh filter ''
/bin/bash ./run.sh action '{"op":"add","amount":250}'
/bin/bash ./run.sh filter status
```

## Alfred 接入参考

- [Script Filter JSON 格式](https://www.alfredapp.com/help/workflows/inputs/script-filter/json/)
- [工作流环境变量与持久化目录](https://www.alfredapp.com/help/workflows/script-environment-variables/)
- [工作流配置页](https://www.alfredapp.com/help/workflows/workflow-configuration/)
