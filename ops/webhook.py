#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub Webhook 接收器：push 到指定分支时自动执行 ops/deploy.sh

零依赖，只用标准库。建议只监听 127.0.0.1，由 Nginx 反代并加 HTTPS。

启动:
    set -a; . .deploy/shared/.env; set +a
    python3 ops/webhook.py            # 默认 127.0.0.1:9100

GitHub 仓库设置 → Webhooks → Add webhook:
    Payload URL : https://你的域名/hooks/github
    Content type: application/json
    Secret      : 与 OPS_WEBHOOK_SECRET 一致
    Events      : Just the push event
"""

import hashlib
import hmac
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
OPS_DIR = APP_DIR / "ops"
DEPLOY_DIR = APP_DIR / ".deploy"
LOCK_FILE = DEPLOY_DIR / "ops.lock"
LOG_FILE = DEPLOY_DIR / "webhook.log"

HOST = os.getenv("OPS_WEBHOOK_HOST", "127.0.0.1")
PORT = int(os.getenv("OPS_WEBHOOK_PORT", "9100"))
SECRET = os.getenv("OPS_WEBHOOK_SECRET", "")
BRANCH = os.getenv("OPS_BRANCH", "main")
DEPLOY_REF = os.getenv("OPS_DEPLOY_REF", "")


def log(msg: str) -> None:
    line = f"[{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def verify(signature: str, body: bytes) -> bool:
    if not SECRET:
        # 没配密钥时拒绝，避免任何人不带签名就能触发发布
        return False
    expected = "sha256=" + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")


def deploy_running() -> bool:
    """用非阻塞 flock 探测是否已有发布在跑

    非 Linux 环境没有 fcntl，此时交给 deploy.sh 自己的锁兜底。
    """
    try:
        import fcntl
    except ImportError:
        return False

    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        with LOCK_FILE.open("w") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(f, fcntl.LOCK_UN)
                return False
            except BlockingIOError:
                return True
    except OSError:
        return False


def trigger_deploy(reason: str) -> None:
    args = ["bash", str(OPS_DIR / "deploy.sh")]
    if DEPLOY_REF:
        args += ["--ref", DEPLOY_REF]

    # 独立会话启动，父进程退出也不影响构建
    with LOG_FILE.open("a", encoding="utf-8") as out:
        subprocess.Popen(
            args,
            cwd=str(APP_DIR),
            stdout=out,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    log(f"已触发发布：{reason}")


class Handler(BaseHTTPRequestHandler):
    server_version = "OpsWebhook/1.0"

    def _reply(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split("?")[0] in ("/health", "/hooks/github"):
            self._reply(200, {"ok": True, "secret_configured": bool(SECRET)})
            return
        self._reply(404, {"detail": "not found"})

    def do_POST(self):
        if self.path.split("?")[0] not in ("/hooks/github", "/"):
            self._reply(404, {"detail": "not found"})
            return

        length = int(self.headers.get("Content-Length") or 0)
        if length > 2 * 1024 * 1024:
            self._reply(413, {"detail": "payload 过大"})
            return

        body = self.rfile.read(length)
        if not verify(self.headers.get("X-Hub-Signature-256", ""), body):
            log("签名校验失败，已拒绝")
            self._reply(401, {"detail": "signature mismatch"})
            return

        event = self.headers.get("X-GitHub-Event", "")
        if event == "ping":
            self._reply(200, {"ok": True, "message": "pong"})
            return
        if event != "push":
            self._reply(202, {"ok": True, "message": f"忽略事件 {event}"})
            return

        try:
            data = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._reply(400, {"detail": "invalid json"})
            return

        ref = data.get("ref", "")
        if ref != f"refs/heads/{BRANCH}":
            self._reply(202, {"ok": True, "message": f"忽略分支 {ref}"})
            return

        if deploy_running():
            log("已有发布在进行，本次 webhook 跳过")
            self._reply(202, {"ok": True, "message": "已有发布在进行中"})
            return

        commits = data.get("commits") or []
        head = (data.get("head_commit") or {}).get("id", "")[:7]
        trigger_deploy(f"{head} {commits[0]['message'].splitlines()[0][:60] if commits else ''}")
        self._reply(202, {"ok": True, "message": "已开始发布", "commit": head})

    def log_message(self, fmt, *args):
        # 访问日志压到 webhook.log，避免刷屏
        log("HTTP " + (fmt % args))


def main() -> None:
    if not SECRET:
        print("⚠ 未设置 OPS_WEBHOOK_SECRET，所有请求都会被拒绝。", file=sys.stderr)
        print("  在 .deploy/shared/.env 里加一行 OPS_WEBHOOK_SECRET=随机串 后重启本服务。", file=sys.stderr)
    DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
    log(f"webhook 监听 http://{HOST}:{PORT}/hooks/github（分支 {BRANCH}）")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
