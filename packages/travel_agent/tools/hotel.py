from travel_agent.tools.base import BaseMockTool


class HotelTool(BaseMockTool):
    """酒店查询工具，根据用户的旅行需求返回酒店选项。"""

    domain = "hotels"
    description = "酒店查询工具，根据用户的旅行需求，返回 suitable_hotels"

    async def execute(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        budget: float,
        num_travelers: int,
        **kwargs: object,
    ) -> list[dict]:
        return [
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
