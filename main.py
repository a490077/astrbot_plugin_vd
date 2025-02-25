from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from vinda import Vinda

user_dict = {
    "郭鹏": "130556",
    "田友晨": "160994",
    "梁嘉卿": "155826",
    "冼玉梅": "151389",
    "赵坚华": "146262",
    "张智尧": "155347",
    "杨耿楠": "155520",
}


@register("vinda", "pp", "自用vinda助手", "1.0.0", "https://github.com/a490077/astrbot_plugin_vd")
class VindaPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.vinda = Vinda(self.config)
        print(self.config)

    @filter.command("订餐")
    async def helloworld(self, event: AstrMessageEvent):
        """订餐命令"""
        user_name = event.get_sender_name()
        message_str = event.message_str  # 用户发的纯文本消息字符串
        message_chain = event.get_messages()  # 用户所发的消息的消息链
        logger.info(message_chain)

        reply_message = self.vinda.do_order(user_dict.get(user_name)) if user_dict.get(user_name) else "你还不是VIP"
        yield event.plain_result(f"@{user_name} {reply_message}")
