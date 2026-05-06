"""
WTO (World Trade Organization) 贸易数据源
WTO Time Series API - 国际贸易统计、关税、贸易流向数据
API文档: https://api.wto.org/timeseries/v1
"""
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

import requests

from app.data_sources.base import BaseDataSource
from app.data_sources.config_resolver import ConfigResolver
from app.data_sources.rate_limiter import RateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)


# WTO 关键指标
WTO_INDICATORS = {
    "TP_A_0010": {"name": "Merchandise Trade Volume", "name_cn": "商品贸易量", "unit": "Index"},
    "TP_E_0010": {"name": "Exports (Value)", "name_cn": "出口额", "unit": "USD"},
    "TP_I_0010": {"name": "Imports (Value)", "name_cn": "进口额", "unit": "USD"},
    "TP_A_0030": {"name": "Commercial Services Trade", "name_cn": "商业服务贸易", "unit": "USD"},
    "TP_A_0020": {"name": "Agricultural Products", "name_cn": "农产品贸易", "unit": "Index"},
}


class WTOProvider(BaseDataSource):
    """WTO 贸易数据源"""

    name = "Macro/WTO"
    BASE_URL = "https://api.wto.org/timeseries/v1"

    def __init__(self):
        self._api_key = self._resolve_api_key()
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'QuantDinger/1.0',
        })
        if self._api_key:
            self._session.headers['Ocp-Apim-Subscription-Key'] = self._api_key

        self._limiter = RateLimiter(min_interval=1.0, jitter_min=0.3, jitter_max=0.7)
        self._cache: Dict[str, Any] = {}

    def _resolve_api_key(self) -> str:
        """解析 API Key"""
        try:
            key = ConfigResolver.get_api_key("macro_wto", key_type="public")
            if key:
                return key
        except Exception:
            pass
        return os.getenv("WTO_API_KEY", "").strip()

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """发送请求到 WTO API"""
        self._limiter.wait()

        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}

        try:
            resp = self._session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"[WTO] Request failed: {endpoint} - {e}")
            return None

    def get_indicators(self) -> Dict[str, Any]:
        """获取可用指标列表"""
        data = self._make_request("indicators", {"i": "all"})
        return data if data else {}

    def get_trade_data(
        self,
        indicator: str = "TP_A_0010",
        reporter: str = "all",
        partner: str = "default",
        periods: str = "2020-2023",
        products: str = "default",
        limit: int = 100
    ) -> Optional[Dict]:
        """
        获取贸易数据

        Args:
            indicator: 指标代码 (如 TP_A_0010)
            reporter: 报告国家 (如 US, CN)
            partner: 伙伴国家 (default = 全球)
            periods: 时期 (如 2020-2023)
            products: 产品分类
            limit: 返回条数
        """
        params = {
            "i": indicator,
            "r": reporter,
            "p": partner,
            "ps": periods,
            "pc": products,
            "fmt": "json",
            "max": limit,
        }

        return self._make_request("data", params)

    def get_key_indicators(self, reporter: str = "all", limit: int = 10) -> Dict[str, Any]:
        """
        获取关键贸易指标

        Args:
            reporter: 报告国家
            limit: 返回指标数量
        """
        result = {}
        indicators = list(WTO_INDICATORS.keys())[:limit]

        for ind in indicators:
            cache_key = f"wto_indicator:{reporter}:{ind}"
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                if time.time() - cached.get("_ts", 0) < 3600:
                    result[ind] = cached
                    continue

            data = self.get_trade_data(ind, reporter, limit=10)
            if data and isinstance(data, dict):
                try:
                    values = data.get("data", [])
                    if values and isinstance(values, list) and len(values) > 0:
                        # 解析 WTO 格式数据
                        latest = values[-1] if isinstance(values[-1], dict) else None
                        if latest:
                            result[ind] = {
                                "name": WTO_INDICATORS[ind]["name"],
                                "name_cn": WTO_INDICATORS[ind]["name_cn"],
                                "value": latest.get("value"),
                                "date": latest.get("year"),
                                "unit": WTO_INDICATORS[ind]["unit"],
                                "_ts": time.time(),
                            }
                            self._cache[cache_key] = result[ind]
                except (KeyError, TypeError, IndexError) as e:
                    logger.debug(f"[WTO] Failed to parse {ind}: {e}")

        return result

    def get_trade_balance(
        self,
        reporter: str = "all",
        start_year: int = 2020,
        end_year: int = 2024
    ) -> Dict[str, Any]:
        """
        获取贸易差额数据

        Args:
            reporter: 报告国家
            start_year: 开始年份
            end_year: 结束年份
        """
        periods = f"{start_year}-{end_year}"

        # 获取出口
        exports = self.get_trade_data("TP_E_0010", reporter, periods=periods)
        # 获取进口
        imports = self.get_trade_data("TP_I_0010", reporter, periods=periods)

        return {
            "exports": exports,
            "imports": imports,
        }

    def get_reporters(self) -> List[Dict]:
        """获取报告经济体列表"""
        data = self._make_request("reporters")
        if data and isinstance(data, list):
            return data
        return []

    # BaseDataSource interface
    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        """
        获取时间序列数据

        Args:
            symbol: 格式 "INDICATOR:REPORTER" (如 TP_A_0010:US)
            timeframe: 时间周期 (WTO 主要年度数据)
            limit: 返回条数
            before_time: 获取此时间之前的数据
        """
        parts = symbol.upper().split(":")
        indicator = parts[0] if parts else "TP_A_0010"
        reporter = parts[1] if len(parts) > 1 else "all"

        # WTO 主要是年度数据
        years = []
        current_year = datetime.now().year
        for i in range(limit + 5):
            years.append(str(current_year - i))
        periods = "-".join(reversed(years[:10]))

        data = self.get_trade_data(indicator, reporter, periods=periods, limit=limit)

        klines = []
        if data and isinstance(data, dict):
            try:
                values = data.get("data", [])
                if values and isinstance(values, list):
                    for item in values:
                        year = item.get("year") or item.get("period")
                        value = item.get("value")
                        if not year or value is None:
                            continue

                        try:
                            dt = datetime(int(year), 1, 1)
                            ts = int(dt.timestamp())
                            klines.append(self.format_kline(ts, value, value, value, value, 0))
                        except (ValueError, TypeError):
                            continue
            except (KeyError, TypeError) as e:
                logger.error(f"[WTO] Kline parse error: {e}")

        return self.filter_and_limit(klines, limit, before_time)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取最新贸易指标"""
        parts = symbol.upper().split(":")
        indicator = parts[0] if parts else "TP_A_0010"
        reporter = parts[1] if len(parts) > 1 else "all"

        data = self.get_trade_data(indicator, reporter, limit=1)
        if data and isinstance(data, dict):
            try:
                values = data.get("data", [])
                if values and isinstance(values, list) and len(values) > 0:
                    latest = values[-1]
                    return {
                        "last": float(latest.get("value", 0)),
                        "symbol": symbol,
                        "date": latest.get("year", ""),
                        "source": "WTO",
                    }
            except (KeyError, TypeError, ValueError, IndexError):
                pass

        return {"last": 0, "symbol": symbol}