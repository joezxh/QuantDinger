# -*- coding: utf-8 -*-
"""
SimFin Provider — 离线基本面数据
基于 SimFin 免费数据集 (CSV)，提供美股三表（资产负债表/利润表/现金流量表）
数据来源: https://simfin.com/
数据需预下载到 data/fundamentals/simfin/ 目录
"""
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.data_sources.base import BaseDataSource
from app.data_sources.rate_limiter import RateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)

# SimFin 数据目录（相对于项目根目录）
SIMFIN_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "data", "fundamentals", "simfin"
)

# SimFin CSV 文件映射
_SIMFIN_FILES = {
    ("us", "balance", "annual"): "us-balance-annual.csv",
    ("us", "balance", "quarterly"): "us-balance-quarterly.csv",
    ("us", "income", "annual"): "us-income-annual.csv",
    ("us", "income", "quarterly"): "us-income-quarterly.csv",
    ("us", "cashflow", "annual"): "us-cashflow-annual.csv",
    ("us", "cashflow", "quarterly"): "us-cashflow-quarterly.csv",
    ("cn", "balance", "annual"): "cn-balance-annual.csv",
    ("cn", "income", "annual"): "cn-income-annual.csv",
    ("cn", "cashflow", "annual"): "cn-cashflow-annual.csv",
}


def _get_csv_path(market: str, statement_type: str, frequency: str) -> Optional[str]:
    """获取 CSV 文件路径"""
    key = (market, statement_type, frequency)
    filename = _SIMFIN_FILES.get(key)
    if not filename:
        # Try annual as fallback
        key_fallback = (market, statement_type, "annual")
        filename = _SIMFIN_FILES.get(key_fallback)
    if not filename:
        return None
    return os.path.join(SIMFIN_DATA_DIR, filename)


class SimFinProvider(BaseDataSource):
    """SimFin 离线基本面数据源

    基于 SimFin 免费数据集的 CSV 文件，提供美股三表数据。
    无需 API Key，但需预先下载数据文件。

    数据下载方式：
    1. 注册 https://simfin.com/ 免费账号
    2. 下载 US 股票的 balance/income/cashflow CSV
    3. 放到 data/fundamentals/simfin/ 目录
    """

    name = "Fundamentals/SimFin"

    def __init__(self):
        self._limiter = RateLimiter(min_interval=0.1)
        self._cache: Dict[str, Any] = {}
        self._data_available = os.path.isdir(SIMFIN_DATA_DIR)

    def is_data_available(self) -> bool:
        """检查 SimFin 数据文件是否存在"""
        return self._data_available

    def _load_csv(self, filepath: str) -> Optional[Any]:
        """加载 CSV 文件（使用 pandas 如可用，否则 csv 模块）"""
        if not os.path.isfile(filepath):
            return None

        self._limiter.wait()

        try:
            import pandas as pd
            return pd.read_csv(filepath, sep=";")
        except ImportError:
            pass

        # Fallback: 标准 csv 模块
        try:
            import csv
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                return list(reader)
        except Exception as e:
            logger.error(f"[SimFin] CSV load failed: {filepath} - {e}")
            return None

    def _filter_by_ticker(
        self, data: Any, ticker: str, curr_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """按股票代码和日期过滤数据"""
        try:
            import pandas as pd
            if isinstance(data, pd.DataFrame):
                df = data[data["Ticker"] == ticker]
                if curr_date and "Publish Date" in df.columns:
                    df["Publish Date"] = pd.to_datetime(df["Publish Date"], utc=True)
                    cutoff = pd.to_datetime(curr_date, utc=True)
                    df = df[df["Publish Date"] <= cutoff]
                return df.to_dict("records")
        except ImportError:
            pass

        # Fallback: list of dicts
        if isinstance(data, list):
            results = [row for row in data if row.get("Ticker") == ticker]
            if curr_date and results:
                results = [
                    row for row in results
                    if row.get("Publish Date", "") <= curr_date
                ]
            return results

        return []

    def get_balance_sheet(
        self,
        ticker: str,
        frequency: str = "annual",
        curr_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取资产负债表"""
        filepath = _get_csv_path("us", "balance", frequency)
        if not filepath:
            return []

        data = self._load_csv(filepath)
        if data is None:
            return []

        return self._filter_by_ticker(data, ticker, curr_date)

    def get_income_statements(
        self,
        ticker: str,
        frequency: str = "annual",
        curr_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取利润表"""
        filepath = _get_csv_path("us", "income", frequency)
        if not filepath:
            return []

        data = self._load_csv(filepath)
        if data is None:
            return []

        return self._filter_by_ticker(data, ticker, curr_date)

    def get_cash_flow_statements(
        self,
        ticker: str,
        frequency: str = "annual",
        curr_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取现金流量表"""
        filepath = _get_csv_path("us", "cashflow", frequency)
        if not filepath:
            return []

        data = self._load_csv(filepath)
        if data is None:
            return []

        return self._filter_by_ticker(data, ticker, curr_date)

    def get_all_financials(
        self,
        ticker: str,
        frequency: str = "annual",
        curr_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取三表汇总"""
        return {
            "ticker": ticker,
            "frequency": frequency,
            "balance_sheet": self.get_balance_sheet(ticker, frequency, curr_date),
            "income_statements": self.get_income_statements(ticker, frequency, curr_date),
            "cash_flow": self.get_cash_flow_statements(ticker, frequency, curr_date),
        }

    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """获取基本面数据（统一接口）"""
        curr_date = datetime.now().strftime("%Y-%m-%d")
        financials = self.get_all_financials(symbol, curr_date=curr_date)

        if not any(financials.get(k) for k in ("balance_sheet", "income_statements", "cash_flow")):
            return {}

        return financials

    # BaseDataSource interface
    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        """SimFin 不提供 K 线数据"""
        return []

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """SimFin 不提供实时报价，返回基本面摘要"""
        fundamentals = self.get_fundamentals(symbol)
        if fundamentals:
            # Extract latest income statement for a quick value
            income = fundamentals.get("income_statements", [])
            latest_revenue = None
            if income:
                try:
                    latest_revenue = float(income[0].get("Revenue", 0))
                except (ValueError, TypeError):
                    pass
            return {
                "last": latest_revenue or 0,
                "symbol": symbol,
                "source": "SimFin",
                "type": "fundamentals",
            }
        return {"last": 0, "symbol": symbol}
