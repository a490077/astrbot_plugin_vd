from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from data.plugins.astrbot_plugin_vd.vinda import Vinda
from astrbot.core.star.filter.permission import PermissionType
import re
import requests
import json
import datetime


# 读取 JSON 配置文件
def load_config(file_path="config.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            logger.info(f"加载配置文件: {file_path}")
            logger.info(f"配置文件内容: {file}")
            return json.load(file)  # 直接返回字典
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"配置文件错误: {e}")
        return {}


conf = load_config()
wx_id_dict = conf.get("wx_id_dict", {})
user_dict = conf.get("user_dict", {})

logger.info(f"conf: {conf}")
logger.info(f"wx_id_dict: {wx_id_dict}")
logger.info(f"user_dict: {user_dict}")


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
        reply_message = self.vinda.菜单()
        yield event.plain_result(reply_message)

    @filter.command("稽查")
    async def 稽查(self, event: AstrMessageEvent):
        """查询今日订餐情况"""
        logger.info("稽查...")
        reply_message = self.vinda.稽查(user_dict)
        yield event.plain_result(reply_message)

    @filter.command("订餐")
    async def 订餐(self, event: AstrMessageEvent, args_str: str = None):
        """给自己或指定用户订餐"""
        logger.info("订餐...")
        async for result in self._CMD(event, self.vinda.do_order, args_str):
            yield result

    @filter.command("销餐")
    async def 销餐(self, event: AstrMessageEvent, args_str: str = None):
        """给自己或指定用户销餐"""
        logger.info("销餐...")
        async for result in self._CMD(event, self.vinda.pin_meal, args_str):
            yield result

    async def _CMD(self, event: AstrMessageEvent, cmd, args_str: str = None):
        """执行命令核心代码, 传入命令和目标用户, 如果没有目标用户则默认为发送者, 只有管理员可以操作其它用户"""
        sender_id = event.get_sender_id()
        sender_name = event.get_sender_name()
        if args_str:
            if not event.is_admin():
                yield event.plain_result("没有权限!...")
                return
        else:
            args_str = wx_id_dict.get(sender_id, sender_name)
        separators = r"[,\s;|:#]+"  # 逗号、空格、分号、竖线、井号 作为分隔符
        args_list = user_dict.keys() if args_str == "ALL" else re.split(separators, args_str)
        logger.info(f"执行命令: {cmd.__name__}, 参数: {args_list}")
        reply_message = "🤡🤡🤡"
        for user_name in args_list:
            if user_name in user_dict:
                reply_message += f"\n@{user_name} {cmd(user_dict.get(user_name))}"
            elif user_name.isdigit():
                reply_message += f"\n@{user_name} {cmd(user_name)}"
            else:
                reply_message += f"\n@{user_name} 你还不是VIP"
        yield event.plain_result(reply_message)

    @filter.command("二维码")
    async def 二维码(self, event: AstrMessageEvent, args_str: str = None):
        """获取用餐二维码"""
        logger.info("二维码...")
        sender_id = event.get_sender_id()
        sender_name = event.get_sender_name()
        if args_str:
            if not event.is_admin():
                yield event.plain_result("没有权限!...")
                return
        else:
            args_str = wx_id_dict.get(sender_id, sender_name)
        if args_str in user_dict:
            args_str = user_dict.get(args_str)  # 参数转为工号
        elif not str(args_str).isdigit():
            yield event.plain_result(f"@{args_str} 你还不是VIP")
            return
        qr = self.vinda.get_qr_code_data(args_str)  # 返回二维码路径
        if qr:
            yield event.image_result(qr)
        else:
            yield event.plain_result("获取二维码失败")

    @filter.command("查询")
    async def 查询(self, event: AstrMessageEvent, name: str = None):
        """根据名称查询员工信息"""
        logger.info("查询...")
        reply_message = self.vinda.查询(name)
        yield event.plain_result(reply_message)

    @filter.llm_tool()
    async def check_order_meals(self, event: AstrMessageEvent):
        """无需参数, 返回各成员的订餐情况。
        或者用户问到:谁是小丑?时也可以以此结果回复
        """
        async for result in self.稽查(event):
            return result

    @filter.llm_tool()
    async def check_menu(self, event: AstrMessageEvent):
        """无需参数, 返回饭堂的菜单
        用户询问吃什么的时候可以以此结果回复
        """
        async for result in self.菜单(event):
            yield result

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def v_me_50(self, event: AstrMessageEvent):
        """疯狂星期四V50"""
        today = datetime.datetime.today()
        today.isoweekday()
        pattern = r"([Vv]我?50|疯狂星期四|今天星期四|[Kk][Ff][Cc]|星期几|肯德基)"
        if today.isoweekday() == 4 and bool(re.search(pattern, event.message_str)):
            url = "https://vme.im/api?format=text"
            try:
                response = requests.get(url)  # 设置超时防止长时间等待
                response.raise_for_status()  # 检查 HTTP 响应状态码
                result_text = response.text  # 直接获取文本
            except requests.exceptions.RequestException as e:
                result_text = f"获取信息失败: {e}"

            yield event.plain_result(result_text)

    @filter.command("摸鱼")
    async def 摸鱼(self, event: AstrMessageEvent):
        """摸鱼日历"""
        yield event.image_result("https://api.52vmy.cn/api/wl/moyu")
