"""
东方财富新闻数据源
通过AKShare/东方财富接口获取A股财经新闻
"""
import time
from typing import Dict, List, Any, Optional

from app.data_sources.base import BaseDataSource
from app.data_sources.rate_limiter import get_akshare_limiter
from app.utils.logger import get_logger

logger = get_logger(__name__)

_AKSHARE_AVAILABLE = False
try:
    import akshare as ak
    _AKSHARE_AVAILABLE = True
except ImportError:
    pass


class EastMoneyNewsProvider(BaseDataSource):
    """东方财富新闻数据源"""

    name = "News/EastMoney"

    def __init__(self):
        self._ak = ak if _AKSHARE_AVAILABLE else None
        self._limiter = get_akshare_limiter()

    def get_stock_news(self, symbol: str, limit: int = 20) -> List[Dict]:
        """
        获取个股新闻

        Args:
            symbol: 股票代码，如 '000001'
            limit: 返回数量
        """
        if not self._ak:
            return []

        self._limiter.wait()

        try:
            df = self._ak.stock_news_em(symbol=symbol)
            if df is None or df.empty:
                return []

            results = []
            for _, row in df.head(limit).iterrows():
                results.append({
                    "title": row.get("新闻标题", ""),
                    "content": row.get("新闻内容", ""),
                    "source": row.get("文章来源", ""),
                    "published": str(row.get("发布时间", "")),
                    "url": row.get("新闻链接", ""),
                    "keyword": row.get("关键词", ""),
                })
            return results
        except Exception as e:
            logger.error(f"[EastMoney] get_stock_news failed: {symbol} - {e}")
            return []

    def get_cctv_news(self, limit: int = 20) -> List[Dict]:
        """获取央视新闻联播"""
        if not self._ak:
            return []

        self._limiter.wait()

        try:
            df = self._ak.news_cctv(date=time.strftime("%Y%m%d"))
            if df is None or df.empty:
                return []

            results = []
            for _, row in df.head(limit).iterrows():
                results.append({
                    "title": row.get("title", ""),
                    "content": row.get("content", ""),
                    "published": str(row.get("date", "")),
                    "source": "CCTV",
                })
            return results
        except Exception as e:
            logger.error(f"[EastMoney] get_cctv_news failed: {e}")
            return []

    def get_financial_news(self, limit: int = 20) -> List[Dict]:
        """获取财经快讯"""
        if not self._ak:
            return []

        self._limiter.wait()

        try:
            df = self._ak.stock_info_global_em()
            if df is None or df.empty:
                return []

            results = []
            for _, row in df.head(limit).iterrows():
                results.append({
                    "title": row.get("标题", "") or row.get("title", ""),
                    "content": row.get("内容", "") or row.get("content", ""),
                    "published": str(row.get("发布时间", "")) or str(row.get("datetime", "")),
                    "source": row.get("文章来源", "") or row.get("source", ""),
                    "keyword": row.get("关键字", "") or row.get("keyword", ""),
                })
            return results
        except Exception as e:
            logger.error(f"[EastMoney] get_financial_news failed: {e}")
            return []

    # BaseDataSource interface
    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        return []

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        return {"last": 0, "symbol": symbol}
