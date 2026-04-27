"""Market data collection service with graph-oriented adapters."""
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from typing import Any, Dict, List, Optional

from app.collectors.base import CollectedItem
from app.data_sources.polymarket import PolymarketDataSource
from app.services.kline import KlineService
from app.utils.logger import get_logger
from app.config import APIKeys

logger = get_logger(__name__)


class MarketDataCollector:
    def __init__(self):
        self.kline_service = KlineService()
        self.polymarket_source = PolymarketDataSource()
        self._finnhub_client = None
        self._init_clients()

    def _init_clients(self):
        finnhub_key = APIKeys.FINNHUB_API_KEY
        if finnhub_key:
            try:
                import finnhub
                self._finnhub_client = finnhub.Client(api_key=finnhub_key)
            except Exception as e:
                logger.warning(f"Finnhub client init failed: {e}")

    def collect_all(
        self,
        market: str,
        symbol: str,
        timeframe: str = "1D",
        include_macro: bool = True,
        include_news: bool = True,
        include_polymarket: bool = True,
        include_graph_context: bool = False,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        start_time = time.time()
        data = {
            "market": market,
            "symbol": symbol,
            "timeframe": timeframe,
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "price": None,
            "kline": None,
            "indicators": {},
            "fundamental": {},
            "company": {},
            "crypto_factors": {},
            "macro": {},
            "news": [],
            "sentiment": {},
            "polymarket": [],
            "graph_context": {},
            "graph_items": [],
            "_meta": {"success_items": [], "failed_items": [], "duration_ms": 0},
        }

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._get_price, market, symbol): "price",
                executor.submit(self._get_kline, market, symbol, timeframe, 60): "kline",
                executor.submit(self._get_fundamental, market, symbol): "fundamental",
                executor.submit(self._get_company, market, symbol): "company",
            }
            try:
                for future in as_completed(futures, timeout=min(timeout, 15)):
                    key = futures[future]
                    try:
                        result = future.result(timeout=3)
                        if result:
                            data[key] = result
                            data["_meta"]["success_items"].append(key)
                        else:
                            data["_meta"]["failed_items"].append(key)
                    except Exception as e:
                        logger.warning(f"Core data fetch failed ({key}): {e}")
                        data["_meta"]["failed_items"].append(key)
            except TimeoutError:
                logger.warning(f"Core data fetch timed out for {market}:{symbol}")

        if include_macro:
            data["macro"] = self._get_macro_data(market, timeout=10)
        if include_news:
            news_result = self._get_news(market, symbol, data.get("company", {}).get("name"), timeout=8)
            data["news"] = news_result.get("news", [])
            data["sentiment"] = news_result.get("sentiment", {})
        if include_polymarket:
            data["polymarket"] = self._get_polymarket_events(symbol, market)
        if include_graph_context:
            try:
                from app.graph.context_builder import GraphContextBuilder
                data["graph_context"] = GraphContextBuilder().build(market, symbol)
            except Exception:
                data["graph_context"] = {}

        data["graph_items"] = self.build_graph_collected_items(market, symbol, data)
        data["_meta"]["duration_ms"] = int((time.time() - start_time) * 1000)
        return data

    def build_graph_collected_items(self, market: str, symbol: str, collected_data: Dict[str, Any]) -> List[CollectedItem]:
        items = self._build_news_collected_items(market, symbol, collected_data.get("news") or [])
        items.extend(self._build_polymarket_collected_items(market, symbol, collected_data.get("polymarket") or []))
        items.extend(self._build_macro_collected_items(market, symbol, collected_data.get("macro") or {}))
        return items

    def _build_news_collected_items(self, market: str, symbol: str, news_items: List[Dict[str, Any]]) -> List[CollectedItem]:
        items: List[CollectedItem] = []
        for news in news_items[:10]:
            headline = news.get("headline") or news.get("title")
            if not headline:
                continue
            normalized = {
                "ticker": symbol,
                "headline": headline,
                "summary": news.get("summary") or news.get("description") or "",
                "published_at": news.get("datetime") or news.get("published_at"),
                "url": news.get("url"),
                "source": news.get("source") or news.get("category") or "news",
                "event_time": news.get("datetime") or news.get("published_at"),
            }
            items.append(
                CollectedItem(
                    source="market_data_collector",
                    data_type="stock_news" if market in ("USStock", "HKStock", "CNStock") else "market_news",
                    market=market,
                    symbol=symbol,
                    raw_data=news,
                    normalized_data=normalized,
                    importance_score=0.7,
                    should_build_episode=True,
                    entity_keys={"ticker": symbol},
                    tags=["news", market.lower()],
                )
            )
        return items

    def _build_polymarket_collected_items(self, market: str, symbol: str, polymarket_items: List[Dict[str, Any]]) -> List[CollectedItem]:
        items: List[CollectedItem] = []
        for item in polymarket_items[:5]:
            market_id = str(item.get("market_id") or item.get("id") or "")
            question = item.get("question")
            if not market_id or not question:
                continue
            normalized = {
                "market_id": market_id,
                "question": question,
                "probability": item.get("current_probability"),
                "event_time": item.get("updated_at") or item.get("end_date_iso"),
            }
            items.append(
                CollectedItem(
                    source="polymarket_market_api",
                    data_type="pm_market_snapshot",
                    market="Polymarket",
                    symbol=f"market:{market_id}",
                    raw_data=item,
                    normalized_data=normalized,
                    importance_score=0.68,
                    should_build_episode=True,
                    entity_keys={"market_id": market_id},
                    tags=["polymarket", "prediction_market"],
                )
            )
        return items

    def _build_macro_collected_items(self, market: str, symbol: str, macro_data: Dict[str, Any]) -> List[CollectedItem]:
        if not macro_data:
            return []
        return [
            CollectedItem(
                source="market_data_collector",
                data_type="macro_snapshot",
                market=market,
                symbol=symbol,
                raw_data=macro_data,
                normalized_data={
                    "market": market,
                    "symbol": symbol,
                    "macro": macro_data,
                    "event_time": datetime.utcnow().isoformat(),
                },
                importance_score=0.55,
                should_build_episode=False,
                entity_keys={"symbol": symbol},
                tags=["macro"],
            )
        ]

    def _get_price(self, market: str, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            return self.kline_service.get_realtime_price(market, symbol, force_refresh=True)
        except Exception as e:
            logger.debug(f"Price fetch failed for {market}:{symbol}: {e}")
            return None

    def _get_kline(self, market: str, symbol: str, timeframe: str, limit: int) -> Optional[List[Dict[str, Any]]]:
        try:
            return self.kline_service.get_kline(market, symbol, timeframe, limit=limit)
        except Exception as e:
            logger.debug(f"Kline fetch failed for {market}:{symbol}: {e}")
            return None

    def _get_fundamental(self, market: str, symbol: str) -> Dict[str, Any]:
        if market == "Crypto":
            return {"symbol": symbol, "type": "crypto"}
        if self._finnhub_client and market == "USStock":
            try:
                return self._finnhub_client.company_basic_financials(symbol, "all") or {}
            except Exception as e:
                logger.debug(f"Fundamental fetch failed for {symbol}: {e}")
        return {}

    def _get_company(self, market: str, symbol: str) -> Dict[str, Any]:
        if self._finnhub_client and market == "USStock":
            try:
                return self._finnhub_client.company_profile2(symbol=symbol) or {}
            except Exception as e:
                logger.debug(f"Company fetch failed for {symbol}: {e}")
        return {"symbol": symbol, "name": symbol}

    def _get_macro_data(self, market: str, timeout: int = 10) -> Dict[str, Any]:
        return {"market": market, "status": "placeholder"}

    def _get_news(self, market: str, symbol: str, company_name: Optional[str], timeout: int = 8) -> Dict[str, Any]:
        if self._finnhub_client and market == "USStock":
            try:
                end_date = datetime.utcnow().date()
                start_date = end_date.fromordinal(end_date.toordinal() - 7)
                items = self._finnhub_client.company_news(symbol, _from=str(start_date), to=str(end_date)) or []
                return {"news": items[:10], "sentiment": {"source": "finnhub", "count": len(items[:10])}}
            except Exception as e:
                logger.debug(f"News fetch failed for {symbol}: {e}")
        return {"news": [], "sentiment": {}}

    def _get_polymarket_events(self, symbol: str, market: str) -> List[Dict[str, Any]]:
        if market == "Polymarket":
            return self.polymarket_source.search_markets(symbol, limit=5, use_cache=False)
        return []


def get_market_data_collector() -> MarketDataCollector:
    return MarketDataCollector()
