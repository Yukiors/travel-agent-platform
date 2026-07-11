from travel_agent.tools.base import BaseMockTool


class ExchangeRateTool(BaseMockTool):
    """汇率查询工具，返回常用货币对人民币的汇率。"""

    domain = "exchange_rate"
    description = "汇率查询工具，查询外币对人民币（CNY）的汇率"

    async def execute(
        self,
        from_currency: str = "CNY",
        to_currency: str = "JPY",
        **kwargs: object,
    ) -> dict:
        rates = _EXCHANGE_RATES.get("rates", {})
        base = _EXCHANGE_RATES.get("base", "CNY")

        if from_currency.upper() != base:
            return {
                "from": from_currency.upper(),
                "to": to_currency.upper(),
                "rate": None,
                "note": f"当前仅支持从 {base} 出发的汇率查询",
            }

        target_rate = rates.get(to_currency.upper())
        if target_rate is None:
            return {
                "from": from_currency.upper(),
                "to": to_currency.upper(),
                "rate": None,
                "note": f"不支持的货币: {to_currency}",
            }

        return {
            "from": from_currency.upper(),
            "to": to_currency.upper(),
            "rate": target_rate,
            "updated": _EXCHANGE_RATES.get("updated", ""),
        }


_EXCHANGE_RATES = {
    "base": "CNY",
    "updated": "2026-07-01",
    "rates": {
        "USD": 0.138,
        "EUR": 0.127,
        "JPY": 20.68,
        "KRW": 185.5,
        "THB": 4.95,
        "SGD": 0.186,
        "GBP": 0.109,
        "AUD": 0.211,
        "HKD": 1.08,
        "TWD": 4.42,
        "VND": 3500.0,
        "MYR": 0.645,
        "IDR": 2200.0,
        "PHP": 7.72,
        "INR": 11.5,
    },
}
