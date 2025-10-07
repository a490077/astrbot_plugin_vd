import asyncio
from astrbot import logger


class WechatPadProMaxClient:
    def __init__(self, token: str):
        self.token = token

    async def send_text(self, to: str, message: str):
        logger.info("模拟发送消息:", to, message)

    async def send_image(self, to: str, image_path: str):
        logger.info("模拟发送图片:", to, image_path)
