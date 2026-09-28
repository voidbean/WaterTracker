"""Small, explicit zh/en catalog. Stored events and action payloads stay language-neutral."""

MESSAGES = {
    "zh": {
        "integer_required": "{label}必须是 1–{maximum} 的整数",
        "cup_label": "杯容量（ml）",
        "goal_label": "每日目标（ml）",
        "interval_label": "补水间隔（分钟）",
        "amount_label": "本次饮水量（ml）",
        "day_changed": "日期已变化，请重新输入 water undo",
        "record_changed": "记录已变化或已撤销，请重新输入 water undo",
        "under_minute": "不足 1 分钟",
        "days": "{n} 天",
        "hours": "{n} 小时",
        "minutes": "{n} 分钟",
        "progress": "今日 {total} / {goal} ml · {count} 次",
        "remaining": "距目标还差 {remaining} ml（约 {cups:.1f} 杯）",
        "completed": "目标已完成 · 超出 {extra} ml",
        "no_records": "尚无饮水记录",
        "future_record": "上次记录时间晚于当前时间，请检查系统时钟",
        "since": "距上次喝完 {elapsed}",
        "goal_reached": "已达到自设目标，不再按间隔提示补水",
        "no_time": "暂无时间依据；喝完后记下第一杯吧",
        "clock_error": "系统时间异常，暂不判断补水间隔",
        "due": "已到设定的补水间隔，可以考虑喝水了",
        "not_due": "未到设定间隔 · 约 {minutes} 分钟后再提示",
        "add": "喝完了，记录 {amount} ml",
        "add_hint": "按回车保存；以确认时刻作为饮用完毕时间",
        "nothing_to_undo": "今天还没有可撤销的记录",
        "undo": "撤销今天最后一笔：{amount} ml",
        "undo_hint": "按回车确认，仅撤销这一笔记录",
        "settings": "查看设置与用法",
        "settings_hint": "杯容量、每日目标、补水间隔、语言",
        "settings_values": "每杯 {cup} ml · 每日目标 {goal} ml",
        "settings_edit": "间隔 {interval} 分钟 · 到 Alfred 偏好设置 → 本工作流 → Configure Workflow 修改",
        "usage": "water：查看状态；water add：记录一杯",
        "usage_more": "water 350：记录指定 ml；water undo：撤销今天最后一笔",
        "local_day": "按本地日期统计；记录时间为喝完并确认的时刻",
        "disclaimer": "仅查询时显示间隔提示，不在后台推送；默认数值是可修改的示例，不是医疗建议",
        "command_add": "记录喝完一杯",
        "command_status": "查看今日饮水状态",
        "command_undo": "撤销今天最后一笔",
        "command_help": "查看帮助",
        "autocomplete": "补全 {command}",
        "unknown_input": "无法识别输入",
        "valid_commands": "使用 water、water add、water 350、water undo 或 water settings",
        "invalid_action": "无效操作，请重新输入 water",
        "invalid_undo": "无效撤销操作",
        "unknown_action": "未知操作，请重新输入 water",
        "added": "已记录 {amount} ml。",
        "undone": "已撤销。",
        "separator": "；",
        "invalid_mode": "运行模式必须是 filter 或 action",
        "failed": "饮水记录未完成：{detail}",
        "error_hint": "请检查工作流配置或数据目录；原有记录不会自动清除",
    },
    "en": {
        "integer_required": "{label} must be an integer from 1 to {maximum}",
        "cup_label": "Cup size (ml)",
        "goal_label": "Daily goal (ml)",
        "interval_label": "Interval (minutes)",
        "amount_label": "Drink amount (ml)",
        "day_changed": "The date has changed. Run water undo again",
        "record_changed": "The record changed or was already undone. Run water undo again",
        "under_minute": "less than 1 min",
        "days": "{n} d",
        "hours": "{n} h",
        "minutes": "{n} min",
        "progress": "Today: {total} / {goal} ml · Entries: {count}",
        "remaining": "{remaining} ml to goal (about {cups:.1f} cups)",
        "completed": "Goal reached · {extra} ml above goal",
        "no_records": "No drinks recorded yet",
        "future_record": "The last entry is in the future. Check your system clock",
        "since": "Since last drink: {elapsed}",
        "goal_reached": "Your goal is reached; interval hints are paused",
        "no_time": "No time reference yet; log your first drink when finished",
        "clock_error": "Clock mismatch; interval hint unavailable",
        "due": "Your interval has elapsed; consider having some water",
        "not_due": "Not due yet · Next hint in about {minutes} min",
        "add": "Finished drinking: log {amount} ml",
        "add_hint": "Press Return to save; the confirmation time is used as the finish time",
        "nothing_to_undo": "No entries to undo today",
        "undo": "Undo today's last entry: {amount} ml",
        "undo_hint": "Press Return to confirm; only this entry will be removed",
        "settings": "Settings and usage",
        "settings_hint": "Cup size, daily goal, interval and language",
        "settings_values": "Cup: {cup} ml · Daily goal: {goal} ml",
        "settings_edit": "Interval: {interval} min · Edit in Alfred Preferences → this workflow → Configure Workflow",
        "usage": "water: view status; water add: log one cup",
        "usage_more": "water 350: log a custom amount; water undo: undo today's last entry",
        "local_day": "Grouped by local date; entries are timestamped when confirmed",
        "disclaimer": "Hints appear only on lookup, not in the background. Defaults are examples, not medical advice",
        "command_add": "Log one finished cup",
        "command_status": "View today's water intake",
        "command_undo": "Undo today's last entry",
        "command_help": "View help",
        "autocomplete": "Complete: {command}",
        "unknown_input": "Unrecognized input",
        "valid_commands": "Use water, water add, water 350, water undo or water settings",
        "invalid_action": "Invalid action. Run water again",
        "invalid_undo": "Invalid undo action",
        "unknown_action": "Unknown action. Run water again",
        "added": "Logged {amount} ml. ",
        "undone": "Entry undone. ",
        "separator": "; ",
        "invalid_mode": "Mode must be filter or action",
        "failed": "Water tracker could not complete the request: {detail}",
        "error_hint": "Check the workflow configuration or data folder; existing records are not automatically cleared",
    },
}


def language_from_env(environ):
    """Keep the previous Chinese default for missing or unsupported settings."""
    value = environ.get("language", "zh").strip().lower()
    return value if value in MESSAGES else "zh"


def tr(key, language="zh", **values):
    return MESSAGES[language][key].format(**values)


class UserError(ValueError):
    """Defer translating domain errors until the UI boundary."""

    def __init__(self, key, **values):
        self.key = key
        self.values = values
        super().__init__(self.localized("zh"))

    def localized(self, language):
        values = dict(self.values)
        if "label" in values:
            values["label"] = tr(values["label"], language)
        return tr(self.key, language, **values)
