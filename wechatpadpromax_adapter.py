import asyncio

from astrbot.api.platform import Platform, AstrBotMessage, MessageMember, PlatformMetadata, MessageType
from astrbot.api.event import MessageChain
from astrbot.api.message_components import Plain, Image, Record  # 消息链中的组件，可以根据需要导入
from astrbot.core.platform.astr_message_event import MessageSesion
from astrbot.api.platform import register_platform_adapter
from astrbot import logger
from .wechatpadpromax_webhook_server import WechatPadProMaxWebhook
from .wechatpadpromax_event import WechatPadProMaxMessageEvent
from .wechatpadpromax_client import WechatPadProMaxClient


# 注册平台适配器。第一个参数为平台名，第二个为描述。第三个为默认配置。
@register_platform_adapter(
    "wechat_pp", "wechat pp 自定义适配器", default_config_tmpl={"authcode": "your_authcode", "port": "6196", "host": "0.0.0.0"}
)
class WechatPadProMaxPlatformAdapter(Platform):
    def __init__(self, platform_config: dict, platform_settings: dict, event_queue: asyncio.Queue) -> None:
        super().__init__(event_queue)
        self.config = platform_config  # 上面的默认配置，用户填写后会传到这里
        self.settings = platform_settings  # platform_settings 平台设置。
        self.client = WechatPadProMaxClient(token=self.config.get("authcode"))
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
        # self.webhook_helper = WechatPadProMaxWebhook(self.config, self._event_queue)
        # await self.webhook_helper.start()

        # FakeClient 是我们自己定义的，这里只是示例。这个是其回调函数
        async def on_received(data):
            logger.info(data)
            abm = await self.convert_message(data=data)  # 转换成 AstrBotMessage
            await self.handle_msg(abm)

        # 初始化 FakeClient
        self.client = WechatPadProMaxClient(self.config.get("authcode"))
        self.client.on_message_received = on_received
        logger.info("WechatPadProMax 客户端已初始化，开始监听消息...")
        await self.client.start_polling()  # 持续监听消息，这是个堵塞方法。

    async def convert_message(self, data: dict) -> AstrBotMessage:
        # 将平台消息转换成 AstrBotMessage
        # 这里就体现了适配程度，不同平台的消息结构不一样，这里需要根据实际情况进行转换。
        abm = AstrBotMessage()
        abm.type = MessageType.GROUP_MESSAGE  # 还有 friend_message，对应私聊。具体平台具体分析。重要！
        abm.group_id = data["group_id"]  # 如果是私聊，这里可以不填
        abm.message_str = data["content"]  # 纯文本消息。重要！
        abm.sender = MessageMember(user_id=data["userid"], nickname=data["username"])  # 发送者。重要！
        abm.message = [Plain(text=data["content"])]  # 消息链。如果有其他类型的消息，直接 append 即可。重要！
        abm.raw_message = data  # 原始消息。
        abm.self_id = data["bot_id"]
        abm.session_id = data["userid"]  # 会话 ID。重要！
        abm.message_id = data["message_id"]  # 消息 ID。

        return abm

    async def handle_msg(self, message: AstrBotMessage):
        # 处理消息
        message_event = WechatPadProMaxMessageEvent(
            message_str=message.message_str,
            message_obj=message,
            platform_meta=self.meta(),
            session_id=message.session_id,
            client=self.client,
        )
        self.commit_event(message_event)  # 提交事件到事件队列。不要忘记！
