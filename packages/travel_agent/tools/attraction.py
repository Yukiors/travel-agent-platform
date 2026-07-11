from travel_agent.tools.base import BaseMockTool


class AttractionTool(BaseMockTool):
    """景点和餐厅查询工具，根据用户的旅行需求返回景点和美食推荐。"""

    domain = "attractions"
    description = "景点和餐厅查询工具，根据用户的旅行需求，返回 attractions 和 meals"

    async def execute(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        budget: float,
        num_travelers: int,
        **kwargs: object,
    ) -> list[dict]:
        seed = self._get_seed(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            num_travelers=num_travelers,
        )
        # 返回 6 条（景点 + 餐饮混合）
        return self._select_options(_ATTRACTION_POOL, seed, count=6)


_ATTRACTION_POOL = [
    # === 景点 ===
    {
        "name": "故宫博物院",
        "type": "attraction",
        "description": "明清两代的皇家宫殿，世界最大的古代宫殿建筑群，收藏有大量珍贵文物",
        "recommended_duration": "4-5小时",
        "ticket_price": 60,
        "opening_hours": "08:30-17:00（周一闭馆）",
    },
    {
        "name": "长城（八达岭段）",
        "type": "attraction",
        "description": "世界文化遗产，明长城精华段，雄伟壮观，可乘缆车上山",
        "recommended_duration": "半天",
        "ticket_price": 40,
        "opening_hours": "06:30-19:00",
    },
    {
        "name": "西湖风景区",
        "type": "attraction",
        "description": "世界文化遗产，杭州最著名的景点，环湖步行或骑行，赏十景",
        "recommended_duration": "半天至全天",
        "ticket_price": 0,
        "opening_hours": "全天开放",
    },
    {
        "name": "外滩",
        "type": "attraction",
        "description": "上海地标，黄浦江畔万国建筑博览群，夜景尤为壮观",
        "recommended_duration": "2-3小时",
        "ticket_price": 0,
        "opening_hours": "全天开放",
    },
    {
        "name": "成都大熊猫繁育研究基地",
        "type": "attraction",
        "description": "近距离观察国宝大熊猫，了解大熊猫保护知识，适合亲子游",
        "recommended_duration": "3-4小时",
        "ticket_price": 55,
        "opening_hours": "07:30-18:00",
    },
    {
        "name": "三亚亚龙湾",
        "type": "attraction",
        "description": "全国最优质的海滩之一，沙白水清，适合游泳和潜水",
        "recommended_duration": "半天",
        "ticket_price": 0,
        "opening_hours": "全天开放",
    },
    {
        "name": "兵马俑博物馆",
        "type": "attraction",
        "description": "世界第八大奇迹，秦始皇陵陪葬陶俑，规模宏大震撼人心",
        "recommended_duration": "3-4小时",
        "ticket_price": 120,
        "opening_hours": "08:30-17:00",
    },
    {
        "name": "洪崖洞",
        "type": "attraction",
        "description": "重庆最具特色的吊脚楼建筑群，夜景璀璨，宛如宫崎骏动漫场景",
        "recommended_duration": "2-3小时",
        "ticket_price": 0,
        "opening_hours": "全天开放（夜景最佳）",
    },
    {
        "name": "石林风景区",
        "type": "attraction",
        "description": "世界自然遗产，典型的喀斯特地貌，奇石林立蔚为壮观",
        "recommended_duration": "半天",
        "ticket_price": 130,
        "opening_hours": "08:00-18:00",
    },
    {
        "name": "鼓浪屿",
        "type": "attraction",
        "description": "世界文化遗产，万国建筑汇集，钢琴之岛，适合漫步和拍照",
        "recommended_duration": "全天",
        "ticket_price": 35,
        "opening_hours": "全天开放",
    },
    {
        "name": "天门山国家森林公园",
        "type": "attraction",
        "description": "玻璃栈道惊险刺激，乘坐世界最长索道，山顶云海壮美",
        "recommended_duration": "半天至全天",
        "ticket_price": 258,
        "opening_hours": "08:00-16:30",
    },
    {
        "name": "中山陵",
        "type": "attraction",
        "description": "孙中山先生陵寝，建筑宏伟气势磅礴，登顶可俯瞰南京全景",
        "recommended_duration": "2-3小时",
        "ticket_price": 0,
        "opening_hours": "06:30-18:00",
    },
    # === 餐饮 ===
    {
        "name": "全聚德烤鸭店（前门店）",
        "type": "meal",
        "description": "百年老字号，北京烤鸭的代表，果木挂炉烤制，外酥里嫩",
        "avg_cost": 180,
        "opening_hours": "11:00-21:00",
    },
    {
        "name": "楼外楼（孤山路店）",
        "type": "meal",
        "description": "老字号杭帮菜馆，西湖醋鱼、东坡肉、龙井虾仁为招牌",
        "avg_cost": 120,
        "opening_hours": "10:00-20:30",
    },
    {
        "name": "成都火锅（蜀大侠）",
        "type": "meal",
        "description": "成都必吃火锅，牛油红锅香辣过瘾，毛肚、黄喉新鲜爽脆",
        "avg_cost": 100,
        "opening_hours": "10:00-23:00",
    },
    {
        "name": "南翔馒头店（豫园店）",
        "type": "meal",
        "description": "上海老字号小吃，招牌小笼包皮薄汤鲜，蟹粉小笼为经典",
        "avg_cost": 60,
        "opening_hours": "07:00-19:00",
    },
    {
        "name": "回民街小吃",
        "type": "meal",
        "description": "西安最著名的美食街，羊肉泡馍、肉夹馍、凉皮、biangbiang面汇聚",
        "avg_cost": 50,
        "opening_hours": "各店时间不一，一般 08:00-22:00",
    },
    {
        "name": "第一市场海鲜加工",
        "type": "meal",
        "description": "三亚最地道的海鲜体验，市场自选新鲜海鲜，周边加工店现做",
        "avg_cost": 150,
        "opening_hours": "06:00-19:00（市场）",
    },
]
