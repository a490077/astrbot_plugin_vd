import asyncio

from astrbot.api.platform import Platform, AstrBotMessage, MessageMember, PlatformMetadata, MessageType
from astrbot.api.event import MessageChain
from astrbot.api.message_components import Plain, Image, Record  # 消息链中的组件，可以根据需要导入
from astrbot.core.platform.astr_message_event import MessageSesion
from astrbot.api.platform import register_platform_adapter
from astrbot import logger
from .wechatpadpromax_webhook_server import WechatPadProMaxWebhook
from .wechatpadpromax_event import WechatPadProMaxMessageEvent


# 注册平台适配器。第一个参数为平台名，第二个为描述。第三个为默认配置。
@register_platform_adapter(
    "wechat_pp",
    "wechat pp 自定义适配器",
    default_config_tmpl={
        "authcode": "your_authcode",
        "host": "0.0.0.0",
        "port": "6196",
        "health_path": "/wppm/health",
        "webhook_path": "/wppm/webhook",
    },
)
class WechatPadProMaxPlatformAdapter(Platform):
    def __init__(self, platform_config: dict, platform_settings: dict, event_queue: asyncio.Queue) -> None:
        super().__init__(event_queue)
        self.config = platform_config  # 上面的默认配置，用户填写后会传到这里
        self.settings = platform_settings  # platform_settings 平台设置。
        logger.info(f"config: {self.config}")

    async def send_by_session(self, session: MessageSesion, message_chain: MessageChain):
        # 必须实现
        await super().send_by_session(session, message_chain)

    def meta(self) -> PlatformMetadata:
        # 必须实现，直接像下面一样返回即可。
        return PlatformMetadata(
            name="wechat_pp",
            description="wechat pp 自定义适配器",
            id=self.config.get("id"),
        )

    async def run(self):
        # 必须实现，这里是主要逻辑。
        self.webhook_helper = WechatPadProMaxWebhook(self.config, self._handle_webhook_event)
        await self.webhook_helper.start()

    async def convert_message(self, data: dict) -> AstrBotMessage:
        # 将平台消息转换成 AstrBotMessage
        # 这里就体现了适配程度，不同平台的消息结构不一样，这里需要根据实际情况进行转换。
        abm = AstrBotMessage()
        abm.type = MessageType.FRIEND_MESSAGE  # 还有 friend_message，对应私聊。具体平台具体分析。重要！
        # abm.group_id = data["group_id"]  # 如果是私聊，这里可以不填
        abm.message_str = data.get("text", "")  # 纯文本消息。重要！
        abm.sender = MessageMember(user_id=data.get("fromUser", ""), nickname=data.get("fromNick", ""))  # 发送者。重要！
        abm.message = [Plain(text=data.get("text", ""))]  # 消息链。如果有其他类型的消息，直接 append 即可。重要！
        abm.raw_message = data.get("rawContent", "")  # 原始消息。
        abm.self_id = data.get("toUser", "")  # 机器人自己的 ID。重要！
        abm.session_id = data.get("fromUser", "")  # 会话 ID。重要！
        abm.message_id = data.get("newMsgId", "")  # 消息 ID。
        return abm

    async def handle_msg(self, message: AstrBotMessage):
        # 处理消息
        logger.info(f"处理消息...")
        message_event = WechatPadProMaxMessageEvent(
            message_str=message.message_str,
            message_obj=message,
            platform_meta=self.meta(),
            session_id=message.session_id,
            client=self.webhook_helper,  # 传入客户端实例
        )
        logger.info(f"提交事件...")
        self.commit_event(message_event)  # 提交事件到事件队列。不要忘记！

    async def _handle_webhook_event(self, event_data: dict):
        """处理 Webhook 事件"""
        logger.info(f"转换消息...")
        abm = await self.convert_message(event_data.get("Data", {}).get("messages", {}))
        logger.info(f"转换消息完成...")
        if abm:
            logger.info(f"转换后abm消息: {abm}")
            await self.handle_msg(abm)
