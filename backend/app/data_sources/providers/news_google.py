"""
Google News 新闻数据源
通过 Google News RSS 搜索金融新闻，免费无需 API Key
"""
import time
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from xml.etree import ElementTree

import requests

from app.data_sources.base import BaseDataSource
from app.data_sources.rate_limiter import RateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GoogleNewsProvider(BaseDataSource):
    """Google News 新闻数据源"""

    name = "News/GoogleNews"
    BASE_URL = "https://news.google.com/rss/search"

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        self._limiter = RateLimiter(min_interval=2.0, jitter_min=1.0, jitter_max=3.0)

    def search(
        self,
        query: str,
        before_date: Optional[str] = None,
        after_date: Optional[str] = None,
        limit: int = 15,
        lang: str = "en",
    ) -> List[Dict]:
        """
        搜索新闻

        Args:
            query: 搜索关键词
            before_date: 截止日期 YYYY-MM-DD
            after_date: 起始日期 YYYY-MM-DD
            limit: 返回数量
            lang: 语言
        """
        q = query.replace(" ", "+")
        params = {"q": q, "hl": lang, "gl": "US", "ceid": "US:en"}

        if after_date:
            params["q"] += f"+after:{after_date}"
        if before_date:
            params["q"] += f"+before:{before_date}"

        self._limiter.wait()

        try:
            resp = self._session.get(self.BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
            return self._parse_rss(resp.text, limit)
        except Exception as e:
            logger.error(f"[GoogleNews] Search failed: {query} - {e}")
            return []

    def _parse_rss(self, xml_text: str, limit: int) -> List[Dict]:
        """解析RSS响应"""
        results = []
        try:
            root = ElementTree.fromstring(xml_text)
            for item in root.findall(".//item")[:limit]:
                title = item.find("title")
                link = item.find("link")
                pub_date = item.find("pubDate")
                source = item.find("source")

                title_text = title.text if title is not None else ""
                link_text = link.text if link is not None else ""
                pub_text = pub_date.text if pub_date is not None else ""
                source_text = source.text if source is not None else ""

                if title_text:
                    results.append({
                        "title": title_text,
                        "link": link_text,
                        "published": pub_text,
                        "source": source_text,
                    })
        except ElementTree.ParseError as e:
            logger.error(f"[GoogleNews] RSS parse error: {e}")

        return results

    def get_company_news(self, ticker: str, limit: int = 10) -> List[Dict]:
        """获取公司相关新闻"""
        query = f"{ticker} stock"
        return self.search(query, limit=limit, lang="en")

    def get_cn_finance_news(self, limit: int = 10) -> List[Dict]:
        """获取中文财经新闻"""
        queries = ["股票市场", "A股行情", "财经新闻"]
        all_news = []
        for q in queries:
            news = self.search(q, limit=5, lang="zh-CN")
            all_news.extend(news)
            if len(all_news) >= limit:
                break
        return all_news[:limit]

    def get_global_macro_news(self, limit: int = 10) -> List[Dict]:
        """获取全球宏观经济新闻"""
        queries = ["Federal Reserve interest rate", "global economy outlook", "stock market today"]
        all_news = []
        for q in queries:
            news = self.search(q, limit=5, lang="en")
            all_news.extend(news)
            if len(all_news) >= limit:
                break
        return all_news[:limit]

    # BaseDataSource interface (新闻源不支持K线)
    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        return []

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        return {"last": 0, "symbol": symbol}
