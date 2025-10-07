import asyncio
from astrbot import logger


class WechatPadProMaxClient:
    """模拟一个消息平台，这里 5 秒钟下发一个消息"""

    def __init__(self, token: str):
        self.token = token
        # ...

    async def start_polling(self):
        while True:
            await asyncio.sleep(5)
            logger.info("模拟收到一条新消息")
            await getattr(self, "on_message_received")(
                {
                    "bot_id": "123",
                    "content": "新消息",
                    "username": "zhangsan",
                    "userid": "123",
                    "message_id": "asdhoashd",
                    "group_id": "group123",
                }
            )

    async def send_text(self, to: str, message: str):
        logger.info("发了消息:", to, message)

    async def send_image(self, to: str, image_path: str):
        logger.info("发了消息:", to, image_path)
