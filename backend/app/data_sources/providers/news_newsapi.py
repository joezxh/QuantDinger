"""
NewsAPI 新闻舆情数据源
NewsAPI.org - 全球财经新闻聚合
API文档: https://newsapi.org/docs/endpoints
"""
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

import requests

from app.data_sources.base import BaseDataSource
from app.data_sources.config_resolver import ConfigResolver
from app.data_sources.rate_limiter import RateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NewsAPIProvider(BaseDataSource):
    """NewsAPI 新闻数据源"""

    name = "News/NewsAPI"
    BASE_URL = "https://newsapi.org/v2"

    def __init__(self):
        self._api_key = self._resolve_api_key()
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'QuantDinger/1.0'
        })
        # NewsAPI 免费版 100次/天
        self._limiter = RateLimiter(min_interval=300.0, jitter_min=30.0, jitter_max=60.0)
        self._cache: Dict[str, Any] = {}

    def _resolve_api_key(self) -> str:
        """解析 API Key"""
        try:
            key = ConfigResolver.get_api_key("news_newsapi", key_type="public")
            if key:
                return key
        except Exception:
            pass
        return os.getenv("NEWS_API_KEY", "").strip()

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """发送请求到 NewsAPI"""
        if not self._api_key:
            logger.warning("[NewsAPI] API key not configured")
            return None

        self._limiter.wait()

        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        params["apiKey"] = self._api_key

        try:
            resp = self._session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"[NewsAPI] Request failed: {endpoint} - {e}")
            return None

    def get_top_headlines(
        self,
        category: str = "business",
        country: str = "us",
        query: Optional[str] = None,
        page_size: int = 20
    ) -> List[Dict]:
        """获取头条新闻"""
        params = {
            "category": category,
            "country": country,
            "pageSize": min(page_size, 100)
        }
        if query:
            params["q"] = query

        data = self._make_request("top-headlines", params)
        if data and data.get("status") == "ok":
            return data.get("articles", [])
        return []

    def search_news(
        self,
        query: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        language: str = "en",
        sort_by: str = "publishedAt",
        page_size: int = 20
    ) -> List[Dict]:
        """搜索新闻"""
        params = {
            "q": query,
            "language": language,
            "sortBy": sort_by,
            "pageSize": min(page_size, 100)
        }
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        data = self._make_request("everything", params)
        if data and data.get("status") == "ok":
            return data.get("articles", [])
        return []

    def get_financial_news(
        self,
        limit: int = 20
    ) -> List[Dict]:
        """获取财经新闻"""
        keywords = ["stock market", "economy", "GDP", "Federal Reserve", "inflation"]
        results = []

        for keyword in keywords[:3]:
            articles = self.search_news(
                query=keyword,
                from_date=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                page_size=limit // 3
            )
            results.extend(articles)

        # 去重
        seen = set()
        unique = []
        for article in results:
            url = article.get("url", "")
            if url and url not in seen:
                seen.add(url)
                unique.append(article)

        return unique[:limit]

    def get_company_news(
        self,
        symbol: str,
        limit: int = 20
    ) -> List[Dict]:
        """获取公司相关新闻"""
        return self.search_news(
            query=f"{symbol} stock",
            from_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            page_size=limit
        )

    def get_key_indicators(self, limit: int = 10) -> Dict[str, Any]:
        """获取新闻情绪指标"""
        articles = self.get_financial_news(limit=limit)

        return {
            "total_articles": len(articles),
            "sources": list(set([a.get("source", {}).get("name", "Unknown") for a in articles])),
            "latest_article": articles[0] if articles else None,
        }

    # BaseDataSource interface
    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        """NewsAPI 不提供 K线数据"""
        return []

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取新闻情绪"""
        articles = self.get_company_news(symbol, limit=10)
        return {
            "last": len(articles),
            "symbol": symbol,
            "news_count": len(articles),
            "latest_title": articles[0].get("title") if articles else None,
            "source": "NewsAPI",
        }