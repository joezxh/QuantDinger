# -*- coding: utf-8 -*-
"""
BEA (Bureau of Economic Analysis) 宏观数据源
美国经济分析局，提供 GDP、PCE、个人收入等国民收入与产出账户(NIPA)数据
API文档: https://apps.bea.gov/api/data/
注册: https://www.bea.gov/data/api/register (免费)
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

# BEA API 基础 URL
BEA_BASE_URL = "https://apps.bea.gov/api/data/"

# NIPA 指标映射：指标ID → NIPA表名 + 行号
BEA_NIPA_INDICATORS = {
    "gdp_growth": {"table": "T10101", "line": "1", "name": "Real GDP Growth", "name_cn": "实际GDP增长率", "unit": "%"},
    "nominal_gdp": {"table": "T10105", "line": "1", "name": "Nominal GDP", "name_cn": "名义GDP", "unit": "Bil.$"},
    "real_gdp": {"table": "T10106", "line": "1", "name": "Real GDP (Chained)", "name_cn": "实际GDP(链式)", "unit": "Bil.$"},
    "gdp_deflator": {"table": "T10104", "line": "1", "name": "GDP Price Index", "name_cn": "GDP平减指数", "unit": "Index"},
    "gdp_price_change": {"table": "T10107", "line": "1", "name": "GDP Price Change", "name_cn": "GDP价格变化率", "unit": "%"},
    "pce": {"table": "T10105", "line": "2", "name": "Personal Consumption Expenditures", "name_cn": "个人消费支出", "unit": "Bil.$"},
    "pce_goods": {"table": "T10105", "line": "3", "name": "PCE Goods", "name_cn": "PCE商品", "unit": "Bil.$"},
    "pce_services": {"table": "T10105", "line": "6", "name": "PCE Services", "name_cn": "PCE服务", "unit": "Bil.$"},
    "gross_investment": {"table": "T10105", "line": "7", "name": "Gross Private Domestic Investment", "name_cn": "国内私人总投资", "unit": "Bil.$"},
    "fixed_investment": {"table": "T10105", "line": "8", "name": "Fixed Investment", "name_cn": "固定投资", "unit": "Bil.$"},
    "net_exports": {"table": "T10105", "line": "15", "name": "Net Exports", "name_cn": "净出口", "unit": "Bil.$"},
    "exports": {"table": "T10105", "line": "16", "name": "Exports", "name_cn": "出口", "unit": "Bil.$"},
    "imports": {"table": "T10105", "line": "19", "name": "Imports", "name_cn": "进口", "unit": "Bil.$"},
    "personal_income": {"table": "T20104", "line": "1", "name": "Personal Income", "name_cn": "个人收入", "unit": "Bil.$"},
    "disposable_income": {"table": "T20104", "line": "27", "name": "Disposable Personal Income", "name_cn": "可支配个人收入", "unit": "Bil.$"},
    "saving_rate": {"table": "T20104", "line": "35", "name": "Personal Saving Rate", "name_cn": "个人储蓄率", "unit": "%"},
    "corporate_profits": {"table": "T10105", "line": "12", "name": "Corporate Profits", "name_cn": "企业利润", "unit": "Bil.$"},
    "govt_spending": {"table": "T10105", "line": "22", "name": "Government Spending", "name_cn": "政府支出", "unit": "Bil.$"},
}

# symbol 别名映射：允许用 GDP、PCE 等短名称访问
_SYMBOL_ALIAS = {
    "GDP": "nominal_gdp",
    "GDPC1": "real_gdp",
    "A191RL": "gdp_growth",
    "PCE": "pce",
    "DGDSRL": "pce_goods",
    "DSERRL": "pce_services",
    "GPS": "gross_investment",
    "FPI": "fixed_investment",
    "NETEXP": "net_exports",
    "EXPGS": "exports",
    "IMPGS": "imports",
    "PI": "personal_income",
    "DPI": "disposable_income",
    "PSAVERT": "saving_rate",
    "CP": "corporate_profits",
    "GEXPND": "govt_spending",
}


class BEAProvider(BaseDataSource):
    """BEA 宏观经济数据源"""

    name = "Macro/BEA"

    def __init__(self):
        self._api_key = self._resolve_api_key()
        self._session = requests.Session()
        self._limiter = RateLimiter(min_interval=1.0, jitter_min=0.5, jitter_max=1.5)
        self._cache: Dict[str, Any] = {}

    def _resolve_api_key(self) -> str:
        try:
            key = ConfigResolver.get_api_key("macro_bea", key_type="public")
            if key:
                return key
        except Exception:
            pass
        return os.getenv("BEA_API_KEY", "").strip()

    def _request(self, params: Dict[str, Any]) -> Optional[Dict]:
        """向 BEA API 发送请求"""
        if not self._api_key:
            logger.warning("[BEA] API key not configured")
            return None

        params["UserID"] = self._api_key
        params["ResultFormat"] = "JSON"

        self._limiter.wait()

        try:
            resp = self._session.get(BEA_BASE_URL, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            # BEA API 返回的 JSON 结构: { "BEAAPI": { "Results": {...} } }
            bea_api = data.get("BEAAPI", data)
            if "Error" in bea_api:
                error_msg = bea_api["Error"].get("ErrorDetail", {}).get("Description", str(bea_api["Error"]))
                logger.error(f"[BEA] API error: {error_msg}")
                return None
            return bea_api.get("Results", bea_api)
        except Exception as e:
            logger.error(f"[BEA] Request failed: {e}")
            return None

    def _resolve_indicator(self, symbol: str) -> Optional[Dict]:
        """将 symbol 解析为 NIPA 指标配置"""
        # 直接匹配
        if symbol.lower() in BEA_NIPA_INDICATORS:
            return BEA_NIPA_INDICATORS[symbol.lower()]
        # 别名匹配
        alias = _SYMBOL_ALIAS.get(symbol.upper())
        if alias and alias in BEA_NIPA_INDICATORS:
            return BEA_NIPA_INDICATORS[alias]
        return None

    def get_nipa_data(
        self,
        table_name: str,
        line_number: str = "1",
        year: Optional[str] = None,
        frequency: str = "Q",
    ) -> Optional[Dict]:
        """
        获取 NIPA 表数据

        Args:
            table_name: NIPA 表名，如 'T10101'
            line_number: 行号
            year: 年份（None = 所有可用年）
            frequency: 'A'(年度), 'Q'(季度), 'M'(月度)
        """
        params = {
            "method": "GetData",
            "DatasetName": "NIPA",
            "TableName": table_name,
            "Frequency": frequency,
            "Year": year or "ALL",
        }
        if line_number:
            params["LineNumber"] = line_number

        return self._request(params)

    def get_indicator(
        self,
        indicator_id: str,
        year: Optional[str] = None,
        frequency: str = "Q",
    ) -> Dict[str, Any]:
        """
        获取指标数据（按指标 ID）

        Args:
            indicator_id: 指标 ID，如 'nominal_gdp', 'pce'
            year: 年份
            frequency: 频率

        Returns:
            {indicator_id: {name, name_cn, data: [{date, value}], unit}}
        """
        config = BEA_NIPA_INDICATORS.get(indicator_id.lower())
        if not config:
            return {}

        cache_key = f"bea:{indicator_id}:{frequency}:{year or 'ALL'}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached.get("_ts", 0) < 3600:  # 1h cache
                return cached["result"]

        result_data = self.get_nipa_data(
            table_name=config["table"],
            line_number=config["line"],
            year=year,
            frequency=frequency,
        )

        if not result_data or "Data" not in result_data:
            return {indicator_id: {"name": config["name"], "name_cn": config["name_cn"], "data": [], "unit": config["unit"]}}

        data_points = []
        for row in result_data["Data"]:
            val_str = row.get("DataValue", "").replace(",", "")
            if val_str and val_str not in ("...", "(NA)", "n.a."):
                try:
                    value = float(val_str)
                    period = row.get("TimePeriod", "")
                    data_points.append({"date": period, "value": value})
                except (ValueError, TypeError):
                    continue

        data_points.sort(key=lambda x: x["date"])

        result = {
            indicator_id: {
                "name": config["name"],
                "name_cn": config["name_cn"],
                "data": data_points,
                "unit": config["unit"],
            }
        }
        self._cache[cache_key] = {"result": result, "_ts": time.time()}
        return result

    def get_key_indicators(self, frequency: str = "Q") -> Dict[str, Any]:
        """获取关键宏观指标最新值"""
        results = {}
        for indicator_id, config in list(BEA_NIPA_INDICATORS.items())[:6]:
            data = self.get_indicator(indicator_id, frequency=frequency)
            if indicator_id in data:
                info = data[indicator_id]
                latest = info["data"][-1] if info["data"] else {}
                results[indicator_id] = {
                    "name": config["name"],
                    "name_cn": config["name_cn"],
                    "value": latest.get("value"),
                    "date": latest.get("date"),
                    "unit": config["unit"],
                }
        return results

    def get_dataset_list(self) -> Optional[List[str]]:
        """获取 BEA 可用数据集列表"""
        params = {"method": "GetDataSetList"}
        result = self._request(params)
        if result and "DataSet" in result:
            return [ds.get("DatasetName", "") for ds in result["DataSet"]]
        return None

    # BaseDataSource interface
    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        """
        获取宏观指标 K 线数据

        Args:
            symbol: 指标名或别名，如 'nominal_gdp', 'GDP', 'pce'
            timeframe: 仅支持季度/年度数据
            limit: 数据条数
            before_time: Unix 时间戳
        """
        config = self._resolve_indicator(symbol)
        if not config:
            return []

        frequency = "Q"  # BEA 默认季度
        if timeframe in ("1W", "1M"):
            frequency = "M"
        elif timeframe == "1Y":
            frequency = "A"

        data = self.get_nipa_data(
            table_name=config["table"],
            line_number=config["line"],
            frequency=frequency,
        )

        if not data or "Data" not in data:
            return []

        klines = []
        for row in data["Data"]:
            val_str = row.get("DataValue", "").replace(",", "")
            if not val_str or val_str in ("...", "(NA)", "n.a."):
                continue
            try:
                value = float(val_str)
                period = row.get("TimePeriod", "")
                # 解析 BEA 时间期间格式: 2023Q1, 2023, 2023M01
                ts = self._parse_period(period)
                if ts is None:
                    continue
                klines.append(self.format_kline(ts, value, value, value, value, 0))
            except (ValueError, TypeError):
                continue

        return self.filter_and_limit(klines, limit, before_time)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取指标最新值"""
        config = self._resolve_indicator(symbol)
        if not config:
            return {"last": 0, "symbol": symbol}

        data = self.get_nipa_data(
            table_name=config["table"],
            line_number=config["line"],
            frequency="Q",
        )

        if data and "Data" in data:
            # BEA 返回的数据默认最新在最后
            for row in reversed(data["Data"]):
                val_str = row.get("DataValue", "").replace(",", "")
                if val_str and val_str not in ("...", "(NA)", "n.a."):
                    try:
                        value = float(val_str)
                        return {
                            "last": value,
                            "symbol": symbol,
                            "date": row.get("TimePeriod", ""),
                            "source": "BEA",
                        }
                    except (ValueError, TypeError):
                        continue

        return {"last": 0, "symbol": symbol}

    @staticmethod
    def _parse_period(period: str) -> Optional[int]:
        """解析 BEA 时间期间为 Unix 时间戳"""
        try:
            if "Q" in period:
                # 2023Q1 → 2023-01-01
                year, q = period.split("Q")
                month = (int(q) - 1) * 3 + 1
                dt = datetime(int(year), month, 1)
            elif "M" in period and len(period) == 7:
                # 2023M01 → 2023-01-01
                year = period[:4]
                month = int(period[5:])
                dt = datetime(int(year), month, 1)
            else:
                # 2023 → 2023-01-01
                dt = datetime(int(period), 1, 1)
            return int(dt.timestamp())
        except (ValueError, TypeError):
            return None
