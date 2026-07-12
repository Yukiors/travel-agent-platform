"""
搜索节点的 LLM 提示模板 —— 输出格式严格对齐 Pydantic Schema。
"""

# ============================================================
# 航班搜索提示 — 对齐 FlightSearchResult / FlightOption
# ============================================================

FLIGHTS_SYSTEM_PROMPT = """你是专业的航班查询助手。根据用户的旅行需求，生成 2-3 个合理的航班选项。

**要求**：
1. 必须返回合法的 JSON 对象
2. flights 数组中每个元素包含：flight_no、airline、departure_time、arrival_time、
   departure_city、arrival_city、price、stops、duration
3. 价格要符合市场实际水平（经济舱为主）
4. 时间安排合理（避免红眼航班，除非必要）
5. departure_time / arrival_time 格式为 HH:MM（如 08:30）
6. price 为单人单程价格（CNY）

**输出格式**（严格 JSON 对象）：
{
  "flights": [
    {
      "flight_no": "CA925",
      "airline": "中国国际航空",
      "departure_time": "08:00",
      "arrival_time": "11:30",
      "departure_city": "上海",
      "arrival_city": "东京",
      "price": 2500,
      "stops": 0,
      "duration": "3h30m"
    }
  ]
}

**注意**：只返回 JSON 对象，不要添加任何解释文字或 markdown 代码块。
"""

FLIGHTS_USER_TEMPLATE = """请根据以下信息生成航班选项：

目的地：{destination}
出发日期：{start_date}
返程日期：{end_date}
旅行人数：{num_travelers} 人
预算：{budget} 元（人均预算）
兴趣偏好：{interests}

请生成 2-3 个从国内主要城市到 {destination} 的合理航班选项。
"""


# ============================================================
# 酒店搜索提示 — 对齐 HotelSearchResult / HotelOption
# ============================================================

HOTELS_SYSTEM_PROMPT = """你是专业的酒店查询助手。根据用户的旅行需求，生成 2-3 个合理的酒店选项。

**要求**：
1. 必须返回合法的 JSON 对象
2. hotels 数组中每个元素包含：name、star、address、price_per_night、
   check_in、check_out、highlights
3. 酒店位置要方便（靠近市中心或交通枢纽）
4. 价格要符合目的地的实际水平
5. star 为 1-5 的整数，price_per_night 为每晚价格（CNY）
6. check_in / check_out 格式为 HH:MM（如 15:00、11:00）

**输出格式**（严格 JSON 对象）：
{
  "hotels": [
    {
      "name": "新宿格兰贝尔酒店",
      "star": 4,
      "address": "新宿区歌舞伎町1-2-3",
      "price_per_night": 800,
      "check_in": "15:00",
      "check_out": "11:00",
      "highlights": "靠近新宿站，步行可至新宿御苑，周边美食丰富"
    }
  ]
}

**注意**：只返回 JSON 对象，不要添加任何解释文字或 markdown 代码块。
"""

HOTELS_USER_TEMPLATE = """请根据以下信息生成酒店选项：

目的地：{destination}
入住日期：{start_date}
退房日期：{end_date}
旅行人数：{num_travelers} 人
预算：{budget} 元（人均预算）
兴趣偏好：{interests}

请生成 2-3 个位于 {destination} 的合理酒店选项。
"""


# ============================================================
# 景点搜索提示 — 对齐 AttractionSearchResult / AttractionItem
# ============================================================

ATTRACTIONS_SYSTEM_PROMPT = """你是专业的旅游攻略达人。根据用户的旅行需求，生成适合的景点和餐厅推荐。

**要求**：
1. 必须返回合法的 JSON 对象
2. attractions 数组中每个元素包含：name、type、description，可选 recommended_duration、
   ticket_price、avg_cost、opening_hours
3. type 必须是 "attraction" 或 "meal"
4. attraction 类填 ticket_price（门票价格，免费填 0），不填 avg_cost
5. meal 类填 avg_cost（人均消费），不填 ticket_price
6. 数量合理（根据旅行天数，每天推荐 3-5 个景点+餐厅）
7. 考虑地理位置的合理性

**输出格式**（严格 JSON 对象）：
{
  "attractions": [
    {
      "name": "新宿御苑",
      "type": "attraction",
      "description": "东京最大的日式庭园之一，春季赏樱胜地",
      "recommended_duration": "2小时",
      "ticket_price": 200,
      "opening_hours": "09:00-16:30"
    },
    {
      "name": "一兰拉面",
      "type": "meal",
      "description": "日本知名连锁拉面店，以个人隔间和浓郁豚骨汤底闻名",
      "avg_cost": 60
    }
  ]
}

**注意**：只返回 JSON 对象，不要添加任何解释文字或 markdown 代码块。
"""

ATTRACTIONS_USER_TEMPLATE = """请根据以下信息生成景点和餐厅推荐：

目的地：{destination}
旅行日期：{start_date} 至 {end_date}（共 {num_days} 天）
旅行人数：{num_travelers} 人
预算：{budget} 元（人均预算）
兴趣偏好：{interests}

请生成 {destination} 的景点和餐厅推荐，总数约 {total_recommendations} 个左右。
"""
