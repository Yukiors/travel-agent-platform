from travel_agent.tools.base import BaseMockTool


class WeatherTool(BaseMockTool):
    """天气查询工具，根据目的地和日期返回天气预报。"""

    domain = "weather"
    description = "天气查询工具，根据用户的旅行目的地和日期，返回天气信息"

    async def execute(
        self,
        destination: str = "",
        date: str = "",
        **kwargs: object,
    ) -> dict:
        # 从日期中提取月份
        month = 1
        if date:
            try:
                from datetime import datetime
                parsed = datetime.strptime(date[:7], "%Y-%m")
                month = parsed.month
            except (ValueError, IndexError):
                pass

        seed = self._get_seed(destination=destination, month=month)

        # 按目的地+月份选一条天气数据，兜底用通用数据
        candidates = _WEATHER_DATA.get(destination, _WEATHER_DATA.get("default", []))
        month_data = [w for w in candidates if w["month"] == month]

        if month_data:
            return self._select_options(month_data, seed, count=1)[0]
        # 最终兜底
        return {
            "month": month,
            "high": 22,
            "low": 14,
            "condition": "多云",
            "humidity": 55,
            "tip": "气候宜人，适合出行",
        }


_WEATHER_DATA = {
    "北京": [
        {"month": 1, "high": 2, "low": -8, "condition": "晴", "humidity": 40, "tip": "寒冷干燥，注意保暖防寒"},
        {"month": 4, "high": 20, "low": 8, "condition": "晴间多云", "humidity": 38, "tip": "春季多风，建议携带防风外套"},
        {"month": 7, "high": 32, "low": 23, "condition": "多云", "humidity": 72, "tip": "高温潮湿，注意防暑降温"},
        {"month": 10, "high": 19, "low": 9, "condition": "晴", "humidity": 50, "tip": "秋高气爽，最适合旅游的季节"},
    ],
    "上海": [
        {"month": 1, "high": 8, "low": 1, "condition": "阴", "humidity": 72, "tip": "湿冷寡照，建议穿羽绒服"},
        {"month": 4, "high": 19, "low": 11, "condition": "小雨", "humidity": 75, "tip": "春雨绵绵，记得带伞"},
        {"month": 7, "high": 33, "low": 26, "condition": "晴", "humidity": 80, "tip": "闷热潮湿，注意防晒补水"},
        {"month": 10, "high": 23, "low": 16, "condition": "多云", "humidity": 68, "tip": "舒适宜人，适合户外活动"},
    ],
    "杭州": [
        {"month": 4, "high": 22, "low": 13, "condition": "晴间多云", "humidity": 65, "tip": "西湖春色迷人，适宜出游"},
        {"month": 7, "high": 35, "low": 26, "condition": "晴", "humidity": 75, "tip": "盛夏炎热，西湖边有微风较舒适"},
        {"month": 10, "high": 22, "low": 14, "condition": "晴", "humidity": 60, "tip": "秋日西湖最佳季节，桂花飘香"},
    ],
    "成都": [
        {"month": 4, "high": 22, "low": 14, "condition": "阴", "humidity": 75, "tip": "阴天较多，但不影响出行"},
        {"month": 7, "high": 30, "low": 23, "condition": "多云", "humidity": 80, "tip": "闷热潮湿，火锅配冰粉最佳"},
        {"month": 10, "high": 20, "low": 14, "condition": "阴", "humidity": 78, "tip": "秋意浓，适合逛宽窄巷子"},
    ],
    "三亚": [
        {"month": 1, "high": 26, "low": 19, "condition": "晴", "humidity": 75, "tip": "冬季最佳避寒目的地，海水温暖"},
        {"month": 4, "high": 30, "low": 24, "condition": "晴", "humidity": 78, "tip": "适合下水游泳，注意防晒"},
        {"month": 7, "high": 33, "low": 27, "condition": "雷阵雨", "humidity": 85, "tip": "台风季，出行前关注天气预警"},
        {"month": 10, "high": 31, "low": 25, "condition": "晴", "humidity": 75, "tip": "雨季尾声，适合海边度假"},
    ],
    "default": [
        {"month": 1, "high": 5, "low": -2, "condition": "多云", "humidity": 55, "tip": "冬季出行，注意保暖"},
        {"month": 4, "high": 20, "low": 10, "condition": "晴", "humidity": 50, "tip": "春光明媚，适宜出游"},
        {"month": 7, "high": 32, "low": 24, "condition": "晴", "humidity": 70, "tip": "夏季高温，注意防晒补水"},
        {"month": 10, "high": 21, "low": 12, "condition": "晴", "humidity": 55, "tip": "秋高气爽，适合出行"},
    ],
}
