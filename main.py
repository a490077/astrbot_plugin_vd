from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from data.plugins.astrbot_plugin_vd.vinda import Vinda
from astrbot.core.star.filter.permission import PermissionType

wx_id_dict = {
    "a490077": "郭鹏",
    "Z7weilaikeji": "赵坚华",
    "JJJJJay53": "梁嘉卿",
    "xian-yumei": "冼玉梅",
    "T403823735": "田友晨",
    "_yyyy_-": "张智尧",
    "YGN0313": "杨耿楠",
    "ROTWbla": "周润泽",
    "wxid_qh51xgdw485d22": "赵坚华",
}

user_dict = {
    "郭鹏": "130556",
    "田友晨": "160994",
    "梁嘉卿": "155826",
    "冼玉梅": "151389",
    "赵坚华": "146262",
    "张智尧": "155347",
    # "杨耿楠": "155520",
    # "周润泽": "155892",
}


@register("vinda", "pp", "自用vinda助手", "1.0.0", "https://github.com/a490077/astrbot_plugin_vd")
class VindaPlugin(Star):
    """🤡vinda小助手🤡 V50开通VIP才能使用"""

    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.vinda = Vinda(self.config)
        logger.info(self.config)

    @filter.command("菜单")
    async def 菜单(self, event: AstrMessageEvent):
        """获取今日菜单"""
        reply_message = self.vinda.菜单()
        yield event.plain_result(reply_message)

    @filter.command("稽查")
    async def 稽查(self, event: AstrMessageEvent):
        """查询今日订餐情况"""
        reply_message = self.vinda.稽查(user_dict)
        yield event.plain_result(reply_message)

    @filter.command("订餐")
    async def 订餐(self, event: AstrMessageEvent, args_str: str):
        """给自己或指定用户订餐"""
        sender_id = event.get_sender_id()
        user_name = event.get_sender_name()
        if args_str:
            self.帮订餐(event, user_dict.keys() if args_str.upper() == "ALL" else args_str.split())
            return
        else:
            if sender_id not in wx_id_dict:
                yield event.plain_result(f"@{user_name} 你还不是VIP")
                return
            reply_message = self.vinda.do_order(user_dict.get(wx_id_dict[sender_id]))
            yield event.plain_result(f"@{user_name} {reply_message}")

    @filter.permission_type(PermissionType.ADMIN)
    async def 帮订餐(self, event: AstrMessageEvent, args: list[str]):
        """给指定用户订餐"""
        reply_message = "订餐结果:"
        for user_name in args:
            if user_name in user_dict:
                reply_message += f"\n@{user_name} {self.vinda.do_order(user_dict.get(user_name))}"
            elif user_name.isdigit():
                reply_message += f"\n@{user_name} {self.vinda.do_order(user_name)}"
            else:
                reply_message += f"\n@{user_name} 还不是VIP"
        yield event.plain_result(reply_message)

    @filter.command("销餐")
    async def 销餐(self, event: AstrMessageEvent, args_str: str):
        """给自己或指定用户销餐"""
        sender_id = event.get_sender_id()
        user_name = event.get_sender_name()
        if args_str:
            self.帮销餐(event, user_dict.keys() if args_str.upper() == "ALL" else args_str.split())
            return
        else:
            if sender_id not in wx_id_dict:
                yield event.plain_result(f"@{user_name} 你还不是VIP")
                return
            reply_message = self.vinda.pin_meal(user_dict.get(wx_id_dict[sender_id]))
            yield event.plain_result(f"@{user_name} {reply_message}")

    @filter.permission_type(PermissionType.ADMIN)
    async def 帮销餐(self, event: AstrMessageEvent, args: list[str]):
        """给指定用户销餐"""
        reply_message = "销餐结果:"
        for user_name in args:
            if user_name in user_dict:
                reply_message += f"\n@{user_name} {self.vinda.pin_meal(user_dict.get(user_name))}"
            elif user_name.isdigit():
                reply_message += f"\n@{user_name} {self.vinda.pin_meal(user_name)}"
            else:
                reply_message += f"\n@{user_name} 还不是VIP"
        yield event.plain_result(reply_message)

    @filter.command("二维码")
    async def 二维码(self, event: AstrMessageEvent):
        """获取自己的用餐二维码数据"""
        sender_id = event.get_sender_id()
        user_name = event.get_sender_name()
        if sender_id not in wx_id_dict:
            yield event.plain_result(f"@{user_name} 你还不是VIP")
            return
        reply_message = self.vinda.get_qr_code_data(user_dict.get(wx_id_dict[sender_id]))
        yield event.plain_result(f"@{user_name} {reply_message}")

    @filter.command("查询")
    async def 查询(self, event: AstrMessageEvent, name: str = None):
        """根据名称查询员工信息"""
        reply_message = self.vinda.查询(name)
        yield event.plain_result(reply_message)

    @filter.llm_tool()
    async def get_menu(self, event: AstrMessageEvent):
        """获取今天的菜单, 不用任何参数, 当用户需要查看菜单时, 可以使用这个函数, 例如用户想知道今天吃什么的时候"""
        self.菜单(event)

    @filter.llm_tool()
    async def do_order(self, event: AstrMessageEvent):
        """订餐函数, 用户想要报餐或订餐时调用, 例如用户说订餐、帮我订餐、报餐、帮我报餐, 不用任何参数"""
        self.订餐(event)

    @filter.llm_tool()
    async def pin_meal(self, event: AstrMessageEvent):
        """取消订餐函数, 用户想要取消报餐或取消订餐时调用, 例如用户说销餐、取消订餐, 不用任何参数"""
        self.销餐(event)

    @filter.llm_tool()
    async def looklook(self, event: AstrMessageEvent):
        """查看今天的订餐情况, 当用户想要查询今天有哪些人订餐和没有订餐时调用,
        例如用户想要看看今天的订餐情况, 或者用户说提到 稽查 等词语时调用
        不用任何参数"""
        self.稽查(event)
