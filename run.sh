#!/bin/bash
set -eu
cd -- "$(dirname -- "$0")"
export PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1
# Alfred does not inherit the interactive shell's PATH. Support both Homebrew
# locations, Python.org installations and the system developer tools.
for python in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    if [ -x "$python" ] && "$python" -c 'import sys; sys.exit(sys.version_info < (3, 9))' >/dev/null 2>&1; then
        exec "$python" ./water.py "$@"
    fi
done
selected_language="${language:-zh}"
case "${selected_language//[[:space:]]/}" in
    [eE][nN])
        title='Python 3.9 or newer is required'
        subtitle='Install Python 3 and retry; see the workflow README'
        ;;
    *)
        title='需要 Python 3.9 或更新版本'
        subtitle='安装 Python 3 后重试；详情见工作流 README'
        ;;
esac
if [ "${1:-filter}" = "filter" ]; then
    printf '{"items":[{"title":"%s","subtitle":"%s","valid":false}]}\n' "$title" "$subtitle"
else
    printf '%s. %s\n' "$title" "$subtitle"
fi
exit 1
