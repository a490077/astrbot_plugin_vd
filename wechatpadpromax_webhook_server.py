import asyncio
import quart
import hmac, hashlib, time
from astrbot import logger


class WechatPadProMaxWebhook:
    def __init__(self, config: dict, event_queue: asyncio.Queue = None):
        self.enabled = config.get("enabled", True)
        self.secret = config.get("secret", "your-signature-secret")
        self.include_self = config.get("includeSelfMessage", True)
        self.message_types = config.get("messageTypes", ["*"])
        self.timestamp_skew = config.get("timestampSkewSec", 900)
        self.dedupe_max = config.get("dedupeMax", 5000)

        self._seen = set()
        self.event_queue = event_queue or asyncio.Queue()

        self.host = config.get("host", "0.0.0.0")
        self.port = config.get("port", 6196)

        self.server = quart.Quart(__name__)
        self.server.add_url_rule("/wppm/health", view_func=self.health, methods=["GET"])
        self.server.add_url_rule("/wppm/webhook", view_func=self.webhook, methods=["POST"])
        self.shutdown_event = asyncio.Event()

    def mark_or_seen(self, key: str) -> bool:
        """去重：如果已经见过就返回 True"""
        if not key:
            return False
        if key in self._seen:
            return True
        if len(self._seen) >= self.dedupe_max:
            try:
                self._seen.pop()
            except KeyError:
                pass
        self._seen.add(key)
        return False

    def verify_signature(self, body: dict) -> bool:
        """HMAC-SHA256 签名校验"""
        base = f"{body.get('Wxid')}:{body.get('MessageType')}:{body.get('Timestamp')}"
        expect = hmac.new(self.secret.encode(), base.encode(), hashlib.sha256).hexdigest()
        got = str(body.get("Signature", "")).lower()
        return hmac.compare_digest(expect, got)

    async def health(self):
        """健康检查端点"""
        return {"status": "ok", "enabled": self.enabled}

    async def webhook(self):
        if not self.enabled:
            return quart.abort(503, "Webhook disabled")

        try:
            body = await quart.request.get_json(force=True)
        except Exception:
            return quart.abort(400, "Invalid JSON")

        mtype = body.get("MessageType", "")
        if ("*" not in self.message_types) and (mtype not in self.message_types):
            return {"ok": True, "skipped": "filtered by messageTypes"}

        if not self.include_self and body.get("IsSelf") is True:
            return {"ok": True, "skipped": "self message"}

        if self.secret and not self.verify_signature(body):
            logger.warning("签名校验失败")
            return quart.abort(401, "Signature verify failed")

        ts = int(body.get("Timestamp", 0))
        now = int(time.time())
        if abs(now - ts) > self.timestamp_skew:
            logger.warning("已忽略旧消息")
            return {"ok": False, "warning": "timestamp skew too large"}

        processed, skipped = 0, 0
        for m in (body.get("Data") or {}).get("messages", []) or []:
            key = f"{m.get('newMsgId','')}|{m.get('msgId','')}"
            if self.mark_or_seen(key):
                skipped += 1
            else:
                processed += 1
                # 把事件丢进队列
                # await self.event_queue.put(m)
                logger.info(f"已处理消息事件: {m.get('msgId','')}")

        return {"ok": True, "processedCount": processed, "skippedCount": skipped}

    async def start(self):
        """启动 Webhook 服务器"""
        logger.info(f"WechatPadProMax 适配器启动: http://{self.host}:{self.port}/wppm/webhook")
        await self.server.run_task(
            host=self.host,
            port=self.port,
            shutdown_trigger=self.shutdown_trigger,
        )

    async def shutdown_trigger(self):
        await self.shutdown_event.wait()

    async def stop(self):
        """停止 Webhook 服务器"""
        self.shutdown_event.set()
        logger.info("WechatPadProMax Webhook 服务器已停止")
