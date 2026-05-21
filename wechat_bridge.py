"""
微信个人号桥接模块
基于微信 ilink 机器人 HTTP 网关实现（长轮询 getUpdates + sendMessage）
参考 cc-connect 的 weixin 平台实现，内置扫码登录
"""

import os
import sys
import json
import time
import threading
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Dict, List
import hashlib
import random
import base64


def _log(msg):
    """输出日志到文件，避免污染 stdout/stderr 干扰终端显示"""
    try:
        log_path = Path.home() / ".loopcli" / "wechat.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_path.write_text(
            log_path.read_text(encoding="utf-8", errors="replace") + f"[{ts}] {msg}\n",
            encoding="utf-8",
        )
    except Exception:
        pass

# 配置
DEFAULT_BASE_URL = "https://ilinkai.weixin.qq.com"
DEFAULT_CDN_BASE_URL = "https://novac2c.cdn.weixin.qq.com/c2c"
CHANNEL_VERSION = "loopcli-weixin/1.0"

# 消息类型
MESSAGE_TYPE_USER = 1
MESSAGE_TYPE_BOT = 2
MESSAGE_ITEM_TEXT = 1
MESSAGE_ITEM_VOICE = 3
MESSAGE_STATE_FINISH = 2
SESSION_EXPIRED_ERRCODE = -14


# ─── 扫码登录 ───

def weixin_qr_login(
    api_url: str = DEFAULT_BASE_URL,
    bot_type: str = "3",
    timeout: int = 480,
) -> dict:
    """
    微信 ilink 扫码登录流程
    返回 {"token": ..., "base_url": ..., "user_id": ..., "bot_id": ...}
    """
    base = api_url.rstrip("/")

    # 1. 获取二维码
    _log("[微信] 正在获取登录二维码...")
    qr_url = f"{base}/ilink/bot/get_bot_qrcode?bot_type={bot_type}"
    resp = requests.get(qr_url, timeout=15)
    resp.raise_for_status()
    qr_data = resp.json()

    qr_key = qr_data.get("qrcode", "")
    qr_img_url = qr_data.get("qrcode_img_content", "")

    if not qr_img_url:
        raise Exception("获取二维码失败：服务器未返回二维码")

    _log(f"\n{'='*50}")
    _log("请使用微信扫描下方二维码")
    _log(f"如果无法扫描终端二维码，请在浏览器打开：")
    _log(f"{qr_img_url}")
    _log(f"{'='*50}\n")

    # 尝试在终端打印二维码（使用 qrcode 库）
    _print_terminal_qr(qr_img_url)

    # 2. 轮询扫码状态
    deadline = time.time() + timeout
    scanned_hint = False
    refresh_count = 0

    while time.time() < deadline:
        status_url = f"{base}/ilink/bot/get_qrcode_status?qrcode={qr_key}"
        try:
            s_resp = requests.get(
                status_url,
                headers={"iLink-App-ClientVersion": "1"},
                timeout=40,
            )
            s_resp.raise_for_status()
            s_data = s_resp.json()
        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            _log(f"[微信] 轮询状态出错: {e}")
            time.sleep(2)
            continue

        status = s_data.get("status", "")

        if status == "wait" or status == "":
            time.sleep(2)
            continue
        elif status == "scaned":
            if not scanned_hint:
                _log("\n[微信] 已扫码，请在手机上确认登录...")
                scanned_hint = True
            time.sleep(2)
            continue
        elif status == "expired":
            refresh_count += 1
            if refresh_count > 3:
                raise Exception("二维码多次过期，请重试")
            _log(f"\n[微信] 二维码已过期，正在刷新 ({refresh_count}/3)...")
            resp = requests.get(qr_url, timeout=15)
            resp.raise_for_status()
            qr_data = resp.json()
            qr_key = qr_data.get("qrcode", "")
            qr_img_url = qr_data.get("qrcode_img_content", "")
            _log(f"新二维码链接: {qr_img_url}\n")
            _print_terminal_qr(qr_img_url)
            scanned_hint = False
            continue
        elif status == "confirmed":
            token = s_data.get("bot_token", "").strip()
            bot_id = s_data.get("ilink_bot_id", "").strip()
            user_id = s_data.get("ilink_user_id", "").strip()
            ret_base = s_data.get("baseurl", "").strip() or base

            if not token or not bot_id:
                raise Exception("登录确认但未获取到 token")

            _log(f"\n✅ 微信登录成功！")
            _log(f"   用户: {user_id}")
            _log(f"   机器人: {bot_id}")

            return {
                "token": token,
                "base_url": ret_base,
                "user_id": user_id,
                "bot_id": bot_id,
            }
        else:
            time.sleep(2)

    raise Exception("等待扫码超时，请重试")


def _print_terminal_qr(url: str):
    """尝试在终端打印二维码"""
    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except ImportError:
        # 没有 qrcode 库，只打印 URL
        pass


def weixin_verify_token(api_url: str, token: str) -> bool:
    """验证 token 是否有效"""
    base = api_url.rstrip("/")
    url = f"{base}/ilink/bot/getupdates"
    body = json.dumps({
        "get_updates_buf": "",
        "base_info": {"channel_version": CHANNEL_VERSION}
    }).encode()
    import urllib.request
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("AuthorizationType", "ilink_bot_token")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Length", str(len(body)))

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        return True
    except Exception:
        return False


# ─── WeChatBridge ───

class WeChatBridge:
    """微信个人号桥接器"""

    def __init__(
        self,
        token: str,
        base_url: str = DEFAULT_BASE_URL,
        allow_from: str = "*",
        state_dir: Optional[str] = None,
        long_poll_timeout_ms: int = 35000,
    ):
        self.token = token.strip()
        self.base_url = base_url.rstrip("/") + "/"
        self.allow_from = [x.strip() for x in allow_from.split(",") if x.strip()]
        self.long_poll_timeout = long_poll_timeout_ms / 1000

        if state_dir is None:
            state_dir = Path.home() / ".loopcli" / "wechat"
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.sync_buf_path = self.state_dir / "get_updates.buf"
        self.context_tokens_path = self.state_dir / "context_tokens.json"

        self.running = False
        self.stop_event = threading.Event()
        self.message_handler: Optional[Callable] = None

        self.sync_buf = ""
        self.context_tokens: Dict[str, str] = {}
        self.dedup_cache: Dict[str, float] = {}

        self._load_state()

    def _load_state(self):
        if self.sync_buf_path.exists():
            self.sync_buf = self.sync_buf_path.read_text(encoding="utf-8")
        if self.context_tokens_path.exists():
            try:
                self.context_tokens = json.loads(
                    self.context_tokens_path.read_text(encoding="utf-8")
                )
            except Exception:
                self.context_tokens = {}

    def _save_state(self):
        self.sync_buf_path.write_text(self.sync_buf, encoding="utf-8")
        self.context_tokens_path.write_text(
            json.dumps(self.context_tokens, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _random_uin(self) -> str:
        u = random.randint(0, 0xFFFFFFFF)
        return base64.b64encode(str(u).encode()).decode()

    def _post(self, endpoint: str, data: dict, timeout: float = 15) -> dict:
        url = self.base_url + endpoint.lstrip("/")
        headers = {
            "Content-Type": "application/json",
            "AuthorizationType": "ilink_bot_token",
            "Authorization": f"Bearer {self.token}",
            "X-WECHAT-UIN": self._random_uin(),
        }
        if "msg" not in data:
            data["base_info"] = {"channel_version": CHANNEL_VERSION}

        try:
            response = requests.post(url, json=data, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            return {"ret": 0, "msgs": [], "get_updates_buf": self.sync_buf}
        except Exception as e:
            raise Exception(f"微信 API 请求失败: {e}")

    def get_updates(self) -> List[dict]:
        result = self._post(
            "ilink/bot/getupdates",
            {"get_updates_buf": self.sync_buf, "base_info": {"channel_version": CHANNEL_VERSION}},
            timeout=self.long_poll_timeout + 5,
        )
        if "get_updates_buf" in result:
            self.sync_buf = result["get_updates_buf"]
            self._save_state()
        if result.get("errcode") == SESSION_EXPIRED_ERRCODE:
            raise Exception("微信会话已过期，需要重新扫码登录")
        return result.get("msgs", [])

    def send_message(self, to_user_id: str, content: str, context_token: Optional[str] = None) -> bool:
        if context_token is None:
            context_token = self.context_tokens.get(to_user_id)
        if not context_token:
            raise Exception("缺少 context_token，用户需要先发一条消息")

        # 分片发送（微信限制 ~3800 字符）
        chunks = _split_text(content, 3800)
        for chunk in chunks:
            client_id = f"lc-{hashlib.md5(f'{time.time()}{random.randint(0,0xFFFF)}'.encode()).hexdigest()[:8]}"
            self._post("ilink/bot/sendmessage", {
                "msg": {
                    "from_user_id": "",
                    "to_user_id": to_user_id,
                    "client_id": client_id,
                    "message_type": MESSAGE_TYPE_BOT,
                    "message_state": MESSAGE_STATE_FINISH,
                    "item_list": [{"type": MESSAGE_ITEM_TEXT, "text_item": {"text": chunk}}],
                    "context_token": context_token,
                }
            })
            time.sleep(0.1)
        return True

    def _is_allowed(self, user_id: str) -> bool:
        if "*" in self.allow_from or not self.allow_from:
            return True
        return user_id in self.allow_from

    def _is_duplicate(self, msg: dict) -> bool:
        key = f"{msg.get('from_user_id')}|{msg.get('message_id')}|{msg.get('seq')}|{msg.get('create_time_ms')}|{msg.get('client_id')}"
        now = time.time()
        self.dedup_cache = {k: v for k, v in self.dedup_cache.items() if now - v < 300}
        if key in self.dedup_cache:
            return True
        self.dedup_cache[key] = now
        return False

    def _extract_text(self, msg: dict) -> str:
        texts = []
        for item in msg.get("item_list", []):
            if item.get("type") == MESSAGE_ITEM_TEXT:
                texts.append(item.get("text_item", {}).get("text", ""))
            elif item.get("type") == MESSAGE_ITEM_VOICE:
                texts.append(item.get("voice_item", {}).get("text", "[语音]"))
        return "\n".join(texts).strip()

    def _process_message(self, msg: dict):
        if msg.get("message_type") == MESSAGE_TYPE_BOT:
            return
        from_user_id = msg.get("from_user_id", "")
        if not self._is_allowed(from_user_id) or self._is_duplicate(msg):
            return

        context_token = msg.get("context_token", "")
        if context_token:
            self.context_tokens[from_user_id] = context_token
            self._save_state()

        text = self._extract_text(msg)
        if text and self.message_handler:
            self.message_handler(
                user_id=from_user_id,
                content=text,
                message_id=msg.get("message_id", 0),
                context_token=context_token,
            )

    def poll_loop(self):
        self.running = True
        while self.running and not self.stop_event.is_set():
            try:
                messages = self.get_updates()
                for msg in messages:
                    self._process_message(msg)
            except Exception as e:
                _log(f"[微信] 轮询错误: {e}")
                time.sleep(5)

    def start(self, message_handler: Callable):
        self.message_handler = message_handler
        self.stop_event.clear()
        threading.Thread(target=self.poll_loop, daemon=True).start()
        _log(f"[微信] 已启动")

    def stop(self):
        self.running = False
        self.stop_event.set()
        _log("[微信] 已停止")


# ─── Inbox/Report 处理器 ───

class WeChatInboxHandler:
    """微信消息收发处理器"""

    def __init__(self, bridge: WeChatBridge, inbox_dir: str, report_dir: str):
        self.bridge = bridge
        self.inbox_dir = Path(inbox_dir)
        self.report_dir = Path(report_dir)
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)

        self.processed_reports: set = set()
        self._load_processed_reports()

    def _load_processed_reports(self):
        f = self.bridge.state_dir / "processed_reports.json"
        if f.exists():
            try:
                self.processed_reports = set(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                self.processed_reports = set()

    def _save_processed_reports(self):
        f = self.bridge.state_dir / "processed_reports.json"
        f.write_text(json.dumps(list(self.processed_reports)), encoding="utf-8")

    def handle_incoming_message(self, user_id: str, content: str, message_id: int, context_token: str):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        safe_id = user_id.replace("@", "_").replace(".", "_")
        filename = f"wechat_{safe_id}_{ts}.md"
        filepath = self.inbox_dir / filename

        filepath.write_text(
            f"# 来自微信的消息\n"
            f"- 类型：指令\n"
            f"- 来源：微信 ({user_id})\n"
            f"- 时间：{now_str}\n\n"
            f"## 内容\n\n{content}\n\n"
            f"## 上下文\n\n- User ID: {user_id}\n- Context Token: {context_token}\n",
            encoding="utf-8",
        )
        _log(f"[微信] -> inbox/{filename}")

        # 追加到聊天历史
        history_path = Path("D:/loopcli/logs/wechat_history.jsonl")
        history_path.parent.mkdir(parents=True, exist_ok=True)
        record = json.dumps({
            "time": now_str,
            "from": user_id,
            "content": content,
        }, ensure_ascii=False)
        with open(history_path, "a", encoding="utf-8") as f:
            f.write(record + "\n")

    def _monitor_reports(self):
        while self.bridge.running:
            try:
                for report_file in self.report_dir.glob("*"):
                    if report_file.name in self.processed_reports:
                        continue
                    if report_file.is_dir():
                        continue

                    content = report_file.read_text(encoding="utf-8")
                    self._send_report(report_file.name, content)
                    self.processed_reports.add(report_file.name)
                    self._save_processed_reports()

                time.sleep(3)
            except Exception as e:
                _log(f"[微信] 报告监控错误: {e}")
                time.sleep(5)

    def _send_report(self, filename: str, content: str):
        # 找到有 context_token 的用户发送
        if not self.bridge.context_tokens:
            _log(f"[微信] 跳过报告 {filename}：无可用 context_token（需要先从微信发一条消息）")
            return

        user_id = list(self.bridge.context_tokens.keys())[0]
        # 截断过长内容
        if len(content) > 3800:
            content = content[:3700] + "\n\n... (已截断)"

        try:
            self.bridge.send_message(user_id, content)
            _log(f"[微信] 报告已发送: {filename}")
        except Exception as e:
            _log(f"[微信] 发送报告失败 {filename}: {e}")

    def start(self):
        self.bridge.start(self.handle_incoming_message)
        threading.Thread(target=self._monitor_reports, daemon=True).start()
        _log(f"[微信] inbox: {self.inbox_dir}")
        _log(f"[微信] report: {self.report_dir}")


def _split_text(s: str, max_len: int) -> List[str]:
    if len(s) <= max_len:
        return [s]
    chunks = []
    while s:
        chunks.append(s[:max_len])
        s = s[max_len:]
    return chunks


def create_wechat_bridge(
    token: str,
    inbox_dir: str = "D:/loopcli/main/inbox",
    report_dir: str = "D:/loopcli/main/report",
    **kwargs
) -> WeChatInboxHandler:
    bridge = WeChatBridge(token=token, **kwargs)
    handler = WeChatInboxHandler(bridge, inbox_dir, report_dir)
    handler.start()
    return handler
