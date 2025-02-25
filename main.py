from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from data.plugins.astrbot_plugin_vd.vinda import Vinda

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
    """vinda助手, 需先绑定工号才能使用"""

    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.vinda = Vinda(self.config)
        print(self.config)

    @filter.command("菜单")
    async def 菜单(self, event: AstrMessageEvent):
        """获取今日菜单"""
        reply_message = self.vinda.菜单()
        yield event.plain_result(reply_message)

    @filter.command("稽查")
    async def 稽查(self, event: AstrMessageEvent):
        """查询今日订餐情况"""
        reply_message = self.vinda.稽查()
        yield event.plain_result(reply_message)

    @filter.command("订餐")
    async def 订餐(self, event: AstrMessageEvent):
        """订餐命令"""
        user_name = event.get_sender_name()
        logger.info(self.context.get_config())
        reply_message = self.vinda.do_order(user_dict.get(user_name)) if user_dict.get(user_name) else "你还不是VIP"
        yield event.plain_result(f"@{user_name} {reply_message}")

    @filter.command("销餐")
    async def 销餐(self, event: AstrMessageEvent):
        """销餐命令"""
        user_name = event.get_sender_name()
        reply_message = self.vinda.pin_meal(user_dict.get(user_name)) if user_dict.get(user_name) else "你还不是VIP"
        yield event.plain_result(f"@{user_name} {reply_message}")

    @filter.command("二维码")
    async def 菜单(self, event: AstrMessageEvent):
        """获取今日菜单"""
        user_name = event.get_sender_name()
        reply_message = self.vinda.get_qr_code_data(user_dict.get(user_name)) if user_dict.get(user_name) else "你还不是VIP"
        yield event.plain_result(reply_message)

    @filter.command("查询")
    async def 查询(self, event: AstrMessageEvent, name: str = None):
        """根据名称查询员工信息"""
        reply_message = self.vinda.查询(name)
        yield event.plain_result(reply_message)
