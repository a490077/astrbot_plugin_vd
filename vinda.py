import requests
import datetime
import json
import urllib.parse
from astrbot.api import logger
from pyqrcode import QRCode


# 获取年-月-日
def get_year_month_day():
    today = datetime.date.today()
    year = today.year
    month = str(today.month).zfill(2)  # 确保为两位数
    day = str(today.day).zfill(2)  # 确保为两位数
    return f"{year}-{month}-{day}"


# 获取年-月-周
def get_year_month_week():
    today = datetime.datetime.now()
    year = today.year
    month = today.month
    day = today.day
    first_day = datetime.date(year, month, 1)
    first_day_weekday = first_day.weekday()  # 0-6，0代表周一，6代表周日
    week_of_month = (day + first_day_weekday - 1) // 7 + 1
    return f"{year}-{month}-{week_of_month}"


# 获取年-月
def get_year_month():
    today = datetime.date.today()
    year = today.year
    month = str(today.month).zfill(2)  # 确保为两位数
    return f"{year}-{month}"


class Vinda:
    def __init__(self, config: dict):
        self.shitang_url = config.shitang_url
        self.cookie_url = config.cookie_url
        self.fk_url = config.fk_url
        self.last_update_time = datetime.datetime.min
        self.headers = {}

    # 获取user_wx
    def update_user_wx(self):
        try:
            current_time = datetime.datetime.now()
            check_time = datetime.timedelta(seconds=10)
            if current_time - self.last_update_time > check_time:
                response = requests.get(f"{self.cookie_url}/get_cookie?type=shitang")
                self.headers["Cookie"] = response.text
                self.last_update_time = datetime.datetime.now()
        except Exception as e:
            logger.info("Error:")
            logger.info(e)

    # 获取今日菜单id
    def get_menu_id(self):
        self.update_user_wx()
        ymw = get_year_month_week()
        url = f"{self.shitang_url}/api/rst-wx/weiDaWx/getMealList?cardCode=130556&hallId=1295907093978411010&type=1&yearMonth={ymw}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["menuId"] + "-1"
        except requests.RequestException as e:
            logger.info("Error:")
            logger.info(e)
            return None

    # 获取今日是否订餐
    def get_order(self, vinda_id):
        try:
            # 更新用户信息
            self.update_user_wx()

            # 构建URL
            url = (
                f"{self.shitang_url}/api/rst-wx/weiDaWx/getMyOrderList?cardCode={vinda_id}&yearMonth={get_year_month()}&type=1"
            )

            # 发送HTTP请求
            response = requests.get(url, headers=self.headers)
            result = response.json()
            # 检查响应结果
            if result.get("code") == 200 and result.get("success"):
                orders = result.get("data", {}).get("myOrders", [])
                if isinstance(orders, list):
                    today = get_year_month_day()
                    if any(order.get("date") == today for order in orders):
                        return "已订餐 🐶"
                    return "未订餐 🤡"
            else:
                raise Exception("请求失败或返回数据格式错误")
        except Exception as e:
            logger.info("Error:")
            logger.info(e)
            return "获取失败 ❌"

    # 获取指定id二维码数据
    def get_qr_code_data(self, vinda_id):
        self.update_user_wx()
        url = f"{self.shitang_url}/api/rst-wx/weiDaWx/getQrCode?cardCode={vinda_id}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                return self.create_qr_code(data.get("data"))
        except requests.RequestException as error:
            logger.info("Error:")
            logger.info(error)
            return None

    # 创建二维码图片对象
    def create_qr_code(self, text):
        try:
            qr_code = QRCode(text)
            qr_code.png("qrcode.png", scale=10)
            return "qrcode.png"
        except Exception as e:
            logger.info("Error:")
            logger.info(e)
            return None

    # 订餐指定id
    def do_order(self, vinda_id):
        self.update_user_wx()
        menu_id = self.get_menu_id()
        if not menu_id:
            return "获取菜单失败"

        self.headers["Content-Type"] = "application/json"
        payload = {"cardCode": vinda_id, "groups": [menu_id], "hallId": "1295907093978411010", "type": "1"}

        try:
            response = requests.post(
                f"{self.shitang_url}/api/rst-wx/weiDaWx/doOrder", headers=self.headers, data=json.dumps(payload)
            )
            response.raise_for_status()
            data = response.json()
            logger.info("订餐请求结果: ")
            logger.info(data)
            return data.get("msg", "未知错误")
        except requests.RequestException as e:
            logger.info("Error:")
            logger.info(e)
            return "订餐失败"

    # 获取指定用户已订餐id
    def get_order_id(self, vinda_id):
        self.update_user_wx()
        url = f"{self.shitang_url}/api/rst-wx/weiDaWx/getMyOrderList?cardCode={vinda_id}&yearMonth={get_year_month()}&type=1"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            if "data" in data and "myOrders" in data["data"] and isinstance(data["data"]["myOrders"], list):
                for order in data["data"]["myOrders"]:
                    if order["date"] == get_year_month_day():
                        return order["orderId"]
        except requests.RequestException as error:
            logger.info("Error:")
            logger.info(error)
            return "获取订餐信息失败"

    # 销餐指定id
    def pin_meal(self, vinda_id):
        self.update_user_wx()
        order_id = self.get_order_id(vinda_id)
        if not order_id:
            return "你今天没有订餐"
        if order_id == "获取订餐信息失败":
            return order_id
        url = f"{self.shitang_url}/api/rst-wx/weiDaWx/pinMeal"
        payload = {"cardCode": vinda_id, "orderIds": [order_id]}
        # logger.info(payload)
        try:
            self.headers["Content-Type"] = "application/json;charset=utf-8"
            response = requests.post(url, headers=self.headers, data=json.dumps(payload))
            response.raise_for_status()
            data = response.json()
            logger.info("销餐请求结果: ")
            logger.info(data)
            return data.get("msg", "未知错误")
        except requests.RequestException as error:
            logger.info("Error:")
            logger.info(error)
            return "销餐失败"

    # 获取今日维达菜单
    def 菜单(self):
        try:
            self.update_user_wx()
            ymw = get_year_month_week()
            url = f"{self.shitang_url}/api/rst-wx/weiDaWx/getMealList?cardCode=130556&hallId=1295907093978411010&type=1&yearMonth={ymw}"
            response = requests.get(url, headers=self.headers)
            result = response.json()
            if (
                result.get("code") == 200
                and result.get("success")
                and isinstance(result.get("data"), list)
                and len(result["data"]) > 0
            ):
                today_dishes = result["data"][0]
                return f"今日菜单: {today_dishes['lunchMenuName']}{today_dishes['lunchSoupName']}"
            else:
                logger.info(result)
                raise Exception("请求失败或返回数据格式错误")
        except Exception as e:
            return "获取失败，请稍后再试。"

    def 稽查(self, user_dict: dict):
        str = "今日订餐情况: "
        for vinda_name, vinda_id in user_dict.items():
            response = self.get_order(vinda_id)
            str += f"\n{vinda_name}: {response}"
        return str

    # 获取员工数据
    def 查询(self, name):
        url_parse = urllib.parse.quote(name)
        url = f"{self.fk_url}/autocrud/bpm.ENGINE.bpm_engine_lov_sqltext_query/query?tag_id=140422&layout_id=108221"
        payload = f'_request_data={{"parameter":{{"name":"{url_parse}"}}}}'
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        # 解析响应
        str_result = ""
        try:
            json_data = response.json()  # 将响应解析为 JSON 格式
            # 检查 JSON 数据中的结构
            if "result" in json_data and "record" in json_data["result"] and len(json_data["result"]["record"]) > 0:
                if isinstance(json_data["result"]["record"], dict):
                    employee_list = [json_data["result"]["record"]]
                else:
                    employee_list = json_data["result"]["record"]
                for employee in employee_list:
                    emplname = employee.get("name")
                    empl_id = employee.get("emplid")
                    level = employee.get("manager_level")
                    des = employee.get("des")
                    str_result += f"\n姓名: {emplname}\n工号: {empl_id}\n级别: {level}\n职位: {des}\n"
            else:
                str_result = f"没有找到 {name} 的信息!"
        except ValueError:
            str_result = "响应数据无法解析为 JSON 格式。"
        return str_result
