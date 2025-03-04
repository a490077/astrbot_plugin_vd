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
    "wxid_x2j90wkliqbj21": "梁嘉卿",
    "wxid_2z1wtpv969x121": "张智尧",
    "wxid_xhhx101k3p2i21": "冼玉梅",
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
    """🤡vinda小助手🤡
    🤡V50开通VIP🤡"""

    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.vinda = Vinda(self.config)

    @filter.command("菜单")
    async def 菜单(self, event: AstrMessageEvent):
        """获取今日菜单"""
        logger.info("菜单...")
        yield self.订餐(event)
        reply_message = self.vinda.菜单()
        yield event.plain_result(reply_message)

    @filter.command("稽查")
    async def 稽查(self, event: AstrMessageEvent):
        """查询今日订餐情况"""
        logger.info("稽查...")
        reply_message = self.vinda.稽查(user_dict)
        yield event.plain_result(reply_message)

    @filter.command("订餐")
    async def 订餐(self, event: AstrMessageEvent):
        """给自己订餐"""
        logger.info("订餐...")
        sender_id = event.get_sender_id()
        user_name = event.get_sender_name()
        if sender_id not in wx_id_dict:
            yield event.plain_result(f"@{user_name} 你还不是VIP")
            return
        reply_message = self.vinda.do_order(user_dict.get(wx_id_dict[sender_id]))
        yield event.plain_result(f"@{user_name} {reply_message}")

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("帮订餐")
    async def 帮订餐(self, event: AstrMessageEvent, user_name: str = None):
        """给指定用户订餐"""
        logger.info("帮订餐...")
        if not user_name:
            yield event.plain_result("请指定要订餐的用户")
            return
        reply_message = ""
        if user_name in user_dict:
            reply_message = f"@{user_name} {self.vinda.do_order(user_dict.get(user_name))}"
        elif user_name.isdigit():
            reply_message = f"@{user_name} {self.vinda.do_order(user_name)}"
        else:
            reply_message = f"@{user_name} 还不是VIP"
        yield event.plain_result(reply_message)

    @filter.command("销餐")
    async def 销餐(self, event: AstrMessageEvent, args_str: str = None):
        """给自己销餐"""
        logger.info("销餐...")
        sender_id = event.get_sender_id()
        user_name = event.get_sender_name()
        if sender_id not in wx_id_dict:
            yield event.plain_result(f"@{user_name} 你还不是VIP")
            return
        reply_message = self.vinda.pin_meal(user_dict.get(wx_id_dict[sender_id]))
        yield event.plain_result(f"@{user_name} {reply_message}")

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("帮销餐")
    async def 帮销餐(self, event: AstrMessageEvent, user_name: str = None):
        """给指定用户销餐"""
        logger.info("帮销餐...")
        if not user_name:
            yield event.plain_result("请指定要销餐的用户")
            return
        reply_message = ""
        if user_name in user_dict:
            reply_message += f"@{user_name} {self.vinda.pin_meal(user_dict.get(user_name))}"
        elif user_name.isdigit():
            reply_message += f"@{user_name} {self.vinda.pin_meal(user_name)}"
        else:
            reply_message += f"@{user_name} 还不是VIP"
        yield event.plain_result(reply_message)

    @filter.command("二维码")
    async def 二维码(self, event: AstrMessageEvent):
        """获取自己的用餐二维码数据"""
        logger.info("二维码...")
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
        logger.info("查询...")
        reply_message = self.vinda.查询(name)
        yield event.plain_result(reply_message)

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("test1")
    async def test1(self, event: AstrMessageEvent):
        """test1"""
        logger.info("test1...")
        yield event.plain_result("test1...")

    @filter.command("test2")
    async def test2(self, event: AstrMessageEvent):
        """test2"""
        logger.info("test2...")
        async for _ in self.test1(event):
            yield
