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
@register_platform_adapter("wechat_pp", "wechat pp 自定义适配器", default_config_tmpl={"authcode": "your_authcode"})
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
        self.webhook_helper = WechatPadProMaxWebhook(self.config, self._event_queue)
        await self.webhook_helper.start()

    async def handle_msg(self, message: AstrBotMessage):
        message_event = WechatPadProMaxMessageEvent(
            message_str=message.message_str,
            message_obj=message,
            platform_meta=self.meta(),
            session_id=message.session_id,
            client=self.client,
        )
        self.commit_event(message_event)
