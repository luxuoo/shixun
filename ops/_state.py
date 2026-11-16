#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布状态读写工具（零依赖，供 ops/*.sh 与后端 API 共用）

用法:
    python3 _state.py set  <state.json> key=value [key=value ...]
    python3 _state.py show <state.json>
    python3 _state.py reset <state.json> [status]

写文件走「临时文件 + 原子替换」，避免后端读到半个 JSON。
"""

import json
import os
import sys
import time
import tempfile


def load(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def coerce(value):
    """把 "true"/"12" 这类字符串转成合适的类型，其余保持字符串"""
    low = value.strip().lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("null", "none", ""):
        return None
    try:
        return int(value)
    except ValueError:
        return value


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2

    action, path = sys.argv[1], sys.argv[2]
    data = load(path)

    if action == "set":
        for pair in sys.argv[3:]:
            if "=" not in pair:
                continue
            k, v = pair.split("=", 1)
            data[k.strip()] = coerce(v)
        # 每次写入都刷新时间戳（原来用 setdefault 导致永远停在第一次写入的时间）
        data["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        save(path, data)
        return 0

    if action == "reset":
        status = sys.argv[3] if len(sys.argv) > 3 else "idle"
        data = {"status": status, "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")}
        save(path, data)
        return 0

    if action == "show":
        if data.get("updated_at") is None and "status" not in data:
            print("{}")
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    print(f"未知操作: {action}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
