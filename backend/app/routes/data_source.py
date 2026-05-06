"""
数据源管理 API
提供数据源配置查询、健康状态监控、优先级调整等接口
"""
from flask import Blueprint, request, jsonify

from app.utils.logger import get_logger

logger = get_logger(__name__)

data_source_bp = Blueprint("data_source", __name__, url_prefix="/api/data-sources")


@data_source_bp.route("/", methods=["GET"])
def list_data_sources():
    """获取所有数据源配置"""
    try:
        from app.database.session import get_session
        from app.models.data_source_meta import DataSourceConfig

        with get_session() as session:
            configs = session.query(DataSourceConfig).order_by(
                DataSourceConfig.layer, DataSourceConfig.source_name
            ).all()

            result = []
            for c in configs:
                result.append({
                    "id": c.id,
                    "source_code": c.source_code,
                    "source_name": c.source_name,
                    "layer": c.layer,
                    "market_categories": c.market_categories or [],
                    "enabled": c.enabled,
                    "load_balance_strategy": c.load_balance_strategy,
                    "config_json": c.config_json or {},
                    "api_key_configured": len(c.api_keys) > 0,
                    "notes": c.notes,
                })

            return jsonify({"data_sources": result, "total": len(result)})
    except Exception as e:
        logger.error(f"Failed to list data sources: {e}")
        return jsonify({"error": str(e)}), 500


@data_source_bp.route("/<source_code>", methods=["GET"])
def get_data_source(source_code: str):
    """获取指定数据源配置"""
    try:
        from app.database.session import get_session
        from app.models.data_source_meta import DataSourceConfig

        with get_session() as session:
            config = session.query(DataSourceConfig).filter(
                DataSourceConfig.source_code == source_code
            ).first()

            if not config:
                return jsonify({"error": f"Data source '{source_code}' not found"}), 404

            return jsonify({
                "source_code": config.source_code,
                "source_name": config.source_name,
                "layer": config.layer,
                "market_categories": config.market_categories or [],
                "enabled": config.enabled,
                "load_balance_strategy": config.load_balance_strategy,
                "config_json": config.config_json or {},
                "datasets": [
                    {
                        "dataset_code": d.dataset_code,
                        "dataset_name": d.dataset_name,
                        "return_type": d.return_type,
                    }
                    for d in config.datasets
                ],
            })
    except Exception as e:
        logger.error(f"Failed to get data source {source_code}: {e}")
        return jsonify({"error": str(e)}), 500


@data_source_bp.route("/<source_code>/toggle", methods=["POST"])
def toggle_data_source(source_code: str):
    """启用/禁用数据源"""
    try:
        from app.database.session import get_session
        from app.models.data_source_meta import DataSourceConfig

        body = request.get_json(silent=True) or {}
        enabled = body.get("enabled")

        if enabled is None:
            return jsonify({"error": "Missing 'enabled' field"}), 400

        with get_session() as session:
            config = session.query(DataSourceConfig).filter(
                DataSourceConfig.source_code == source_code
            ).first()

            if not config:
                return jsonify({"error": f"Data source '{source_code}' not found"}), 404

            config.enabled = enabled
            session.flush()

            return jsonify({
                "source_code": config.source_code,
                "enabled": config.enabled,
                "message": f"Data source '{source_code}' {'enabled' if enabled else 'disabled'}",
            })
    except Exception as e:
        logger.error(f"Failed to toggle data source {source_code}: {e}")
        return jsonify({"error": str(e)}), 500


@data_source_bp.route("/health", methods=["GET"])
def get_health_status():
    """获取所有数据源健康状态"""
    try:
        from app.data_sources.priority_router import get_router
        router = get_router()
        status = router.get_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        return jsonify({"error": str(e)}), 500


@data_source_bp.route("/health/<source_code>", methods=["POST"])
def check_source_health(source_code: str):
    """检查指定数据源健康状态"""
    try:
        from app.database.session import get_session
        from app.models.data_source_meta import DataSourceConfig

        with get_session() as session:
            config = session.query(DataSourceConfig).filter(
                DataSourceConfig.source_code == source_code
            ).first()

            if not config:
                return jsonify({"error": f"Data source '{source_code}' not found"}), 404

            import time
            from app.data_sources.config_resolver import ConfigResolver

            healthy = False
            latency_ms = 0
            error_msg = ""

            try:
                start = time.monotonic()

                if source_code == "crypto_ccxt":
                    from app.data_sources.crypto import CryptoDataSource
                    ds = CryptoDataSource()
                    ticker = ds.get_ticker("BTC/USDT")
                    healthy = ticker.get("last", 0) > 0
                elif source_code == "us_stock_yfinance":
                    from app.data_sources.us_stock import USStockDataSource
                    ds = USStockDataSource()
                    ticker = ds.get_ticker("AAPL")
                    healthy = ticker.get("last", 0) > 0
                elif source_code.startswith("macro_fred"):
                    api_key = ConfigResolver.get_api_key(source_code)
                    healthy = bool(api_key)
                elif source_code.startswith("cn_stock_tushare"):
                    token = ConfigResolver.get_api_key(source_code)
                    healthy = bool(token)
                else:
                    healthy = config.enabled

                latency_ms = int((time.monotonic() - start) * 1000)
            except Exception as e:
                error_msg = str(e)
                healthy = False

            # 更新健康状态表
            from app.utils.db_postgres import execute_sql
            execute_sql(
                """INSERT INTO data_source_health (source_code, category, status, latency_ms, last_check_at, last_error)
                   VALUES (%s, %s, %s, %s, NOW(), %s)
                   ON CONFLICT (source_code, category) DO UPDATE SET
                     status = EXCLUDED.status,
                     latency_ms = EXCLUDED.latency_ms,
                     last_check_at = EXCLUDED.last_check_at,
                     last_error = EXCLUDED.last_error,
                     updated_at = NOW()""",
                (source_code, ", ".join(config.market_categories or []), "healthy" if healthy else "unhealthy", latency_ms, error_msg),
            )

            return jsonify({
                "source_code": source_code,
                "status": "healthy" if healthy else "unhealthy",
                "latency_ms": latency_ms,
                "error": error_msg or None,
            })
    except Exception as e:
        logger.error(f"Health check failed for {source_code}: {e}")
        return jsonify({"error": str(e)}), 500


@data_source_bp.route("/router/status", methods=["GET"])
def get_router_status():
    """获取路由器状态"""
    try:
        from app.data_sources.priority_router import get_router
        router = get_router()
        return jsonify(router.get_status())
    except Exception as e:
        logger.error(f"Failed to get router status: {e}")
        return jsonify({"error": str(e)}), 500


@data_source_bp.route("/categories", methods=["GET"])
def list_categories():
    """获取所有数据类别及其数据源"""
    try:
        from app.data_sources.priority_router import get_router, DataCategory
        router = get_router()

        result = {}
        for cat in DataCategory:
            entries = router.get_providers(cat.value)
            result[cat.value] = [
                {
                    "source_code": e.source_code,
                    "priority": e.priority,
                    "provider_name": e.provider.name,
                }
                for e in entries
            ]

        return jsonify({"categories": result})
    except Exception as e:
        logger.error(f"Failed to list categories: {e}")
        return jsonify({"error": str(e)}), 500


@data_source_bp.route("/macro/indicators", methods=["GET"])
def get_macro_indicators():
    """获取关键宏观经济指标"""
    try:
        category = request.args.get("category", "all")
        result = {}

        if category in ("all", "fred"):
            try:
                from app.data_sources.providers.macro_fred import FREDProvider
                fred = FREDProvider()
                result["fred"] = fred.get_key_indicators(limit=10)
            except Exception as e:
                result["fred"] = {"error": str(e)}

        if category in ("all", "bls"):
            try:
                from app.data_sources.providers.macro_bls import BLSProvider
                bls = BLSProvider()
                result["bls"] = bls.get_key_indicators()
            except Exception as e:
                result["bls"] = {"error": str(e)}

        if category in ("all", "worldbank"):
            try:
                from app.data_sources.providers.macro_worldbank import WorldBankProvider
                wb = WorldBankProvider()
                country = request.args.get("country", "all")
                result["worldbank"] = wb.get_key_indicators(country=country)
            except Exception as e:
                result["worldbank"] = {"error": str(e)}

        if category in ("all", "bea"):
            try:
                from app.data_sources.providers.macro_bea import BEAProvider
                bea = BEAProvider()
                result["bea"] = bea.get_key_indicators()
            except Exception as e:
                result["bea"] = {"error": str(e)}

        return jsonify(result)
    except Exception as e:
        logger.error(f"Failed to get macro indicators: {e}")
        return jsonify({"error": str(e)}), 500


@data_source_bp.route("/defi/tvl", methods=["GET"])
def get_defi_tvl():
    """获取DeFi TVL数据"""
    try:
        from app.data_sources.providers.crypto_defillama import DefiLlamaProvider
        provider = DefiLlamaProvider()

        data_type = request.args.get("type", "chains")
        if data_type == "chains":
            data = provider.get_chains_tvl()
        elif data_type == "protocols":
            data = provider.get_protocols()
        elif data_type == "global":
            data = provider.get_global_tvl()
        elif data_type == "dex":
            data = provider.get_dex_volumes()
        else:
            data = provider.get_chains_tvl()

        return jsonify({"data": data, "source": "defillama"})
    except Exception as e:
        logger.error(f"Failed to get DeFi TVL: {e}")
        return jsonify({"error": str(e)}), 500


@data_source_bp.route("/cftc/cot", methods=["GET"])
def get_cot_report():
    """获取CFTC持仓报告"""
    try:
        from app.data_sources.providers.futures_cftc import CFTCProvider
        provider = CFTCProvider()

        commodity = request.args.get("commodity", "BTC")
        limit = int(request.args.get("limit", 52))

        data = provider.get_cot_report(commodity, limit=limit)
        return jsonify({"data": data, "commodity": commodity, "source": "cftc"})
    except Exception as e:
        logger.error(f"Failed to get COT report: {e}")
        return jsonify({"error": str(e)}), 500


@data_source_bp.route("/news", methods=["GET"])
def get_news():
    """获取新闻数据"""
    try:
        source = request.args.get("source", "google")
        query = request.args.get("query", "")
        limit = int(request.args.get("limit", 10))

        if source == "google":
            from app.data_sources.providers.news_google import GoogleNewsProvider
            provider = GoogleNewsProvider()
            if query:
                data = provider.search(query, limit=limit)
            else:
                data = provider.get_global_macro_news(limit=limit)
        elif source == "eastmoney":
            from app.data_sources.providers.news_eastmoney import EastMoneyNewsProvider
            provider = EastMoneyNewsProvider()
            if query:
                data = provider.get_stock_news(query, limit=limit)
            else:
                data = provider.get_financial_news(limit=limit)
        else:
            data = []

        return jsonify({"data": data, "source": source})
    except Exception as e:
        logger.error(f"Failed to get news: {e}")
        return jsonify({"error": str(e)}), 500


@data_source_bp.route("/cboe/history", methods=["GET"])
def get_cboe_history():
    """获取CBOE波动率指数历史数据"""
    try:
        from app.data_sources.providers.futures_cboe import CBOEProvider
        provider = CBOEProvider()

        index_name = request.args.get("index", "VIX")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        data = provider.get_index_history(index_name, start_date=start_date, end_date=end_date)
        return jsonify({"data": data, "index": index_name, "source": "cboe"})
    except Exception as e:
        logger.error(f"Failed to get CBOE history: {e}")
        return jsonify({"error": str(e)}), 500


@data_source_bp.route("/cboe/indices", methods=["GET"])
def get_cboe_indices():
    """获取CBOE可用指数列表"""
    try:
        from app.data_sources.providers.futures_cboe import CBOEProvider
        provider = CBOEProvider()
        data = provider.get_available_indices()
        return jsonify({"indices": data, "source": "cboe"})
    except Exception as e:
        logger.error(f"Failed to get CBOE indices: {e}")
        return jsonify({"error": str(e)}), 500


@data_source_bp.route("/bea/indicators", methods=["GET"])
def get_bea_indicators():
    """获取BEA宏观经济指标数据"""
    try:
        from app.data_sources.providers.macro_bea import BEAProvider
        provider = BEAProvider()

        indicator = request.args.get("indicator", "nominal_gdp")
        year = request.args.get("year")
        frequency = request.args.get("frequency", "Q")

        data = provider.get_indicator(indicator, year=year, frequency=frequency)
        return jsonify({"data": data, "indicator": indicator, "source": "bea"})
    except Exception as e:
        logger.error(f"Failed to get BEA indicators: {e}")
        return jsonify({"error": str(e)}), 500


@data_source_bp.route("/priority/status", methods=["GET"])
def get_priority_status():
    """获取优先级调整器状态"""
    try:
        from app.data_sources.priority_adjuster import get_priority_adjuster
        adjuster = get_priority_adjuster()
        return jsonify(adjuster.get_adjustment_status())
    except Exception as e:
        logger.error(f"Failed to get priority status: {e}")
        return jsonify({"error": str(e)}), 500


@data_source_bp.route("/priority/adjust", methods=["POST"])
def adjust_priorities():
    """手动触发一次优先级调整"""
    try:
        from app.data_sources.priority_adjuster import get_priority_adjuster
        adjuster = get_priority_adjuster()
        results = adjuster.adjust_now()
        return jsonify({"adjusted": results})
    except Exception as e:
        logger.error(f"Failed to adjust priorities: {e}")
        return jsonify({"error": str(e)}), 500


@data_source_bp.route("/fundamentals/<ticker>", methods=["GET"])
def get_fundamentals(ticker: str):
    """获取基本面数据（通过 Fundamentals 类别路由）"""
    try:
        from app.data_sources.priority_router import get_router, DataCategory
        router = get_router()

        frequency = request.args.get("frequency", "annual")

        # Try FinancialDatasets first (highest priority in Fundamentals)
        result = router.route_method(
            DataCategory.FUNDAMENTALS.value, "get_all_financials",
            ticker=ticker, frequency=frequency
        )
        if result:
            return jsonify({"data": result, "ticker": ticker, "source": "router"})

        # Fallback: SimFin
        result = router.route_method(
            DataCategory.FUNDAMENTALS.value, "get_fundamentals", symbol=ticker
        )
        if result:
            return jsonify({"data": result, "ticker": ticker, "source": "router"})

        return jsonify({"data": None, "ticker": ticker, "error": "No fundamentals data available"})
    except Exception as e:
        logger.error(f"Failed to get fundamentals for {ticker}: {e}")
        return jsonify({"error": str(e)}), 500


@data_source_bp.route("/cboe/futures", methods=["GET"])
def get_cboe_futures():
    """获取 VIX 期货期限结构"""
    try:
        from app.data_sources.providers.futures_cboe import CBOEProvider
        provider = CBOEProvider()

        date = request.args.get("date")
        data = provider.get_futures_term_structure(date=date if date else None)
        return jsonify({"data": data, "source": "cboe"})
    except Exception as e:
        logger.error(f"Failed to get CBOE futures: {e}")
        return jsonify({"error": str(e)}), 500
