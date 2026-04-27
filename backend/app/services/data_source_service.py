"""
数据源配置服务
管理 DataSourceConfig 的 CRUD 操作
"""
from typing import Optional, Dict, Any, List
from sqlalchemy import func

from app.database.session import get_session
from app.models.data_source_meta import DataSourceConfig
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DataSourceService:
    """数据源配置服务"""

    def list_configs(
        self,
        layer: Optional[str] = None,
        market_category: Optional[str] = None,
        enabled: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """列出数据源配置"""
        with get_session() as session:
            query = session.query(DataSourceConfig)

            if layer:
                query = query.filter(DataSourceConfig.layer == layer)
            if enabled is not None:
                query = query.filter(DataSourceConfig.enabled == enabled)
            if market_category:
                query = query.filter(
                    DataSourceConfig.market_categories.contains([market_category])
                )
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    (DataSourceConfig.source_code.ilike(search_pattern)) |
                    (DataSourceConfig.source_name.ilike(search_pattern))
                )

            total = query.count()
            items = query.order_by(DataSourceConfig.id).offset(
                (page - 1) * page_size
            ).limit(page_size).all()

            return {
                "items": [self._to_dict(item) for item in items],
                "total": total,
                "page": page,
                "page_size": page_size
            }

    def get_config(self, config_id: int) -> Optional[Dict[str, Any]]:
        """获取单个数据源配置"""
        with get_session() as session:
            config = session.query(DataSourceConfig).filter(
                DataSourceConfig.id == config_id
            ).first()
            return self._to_dict(config) if config else None

    def get_config_by_code(self, source_code: str) -> Optional[Dict[str, Any]]:
        """通过 source_code 获取配置"""
        with get_session() as session:
            config = session.query(DataSourceConfig).filter(
                DataSourceConfig.source_code == source_code
            ).first()
            return self._to_dict(config) if config else None

    def create_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建数据源配置"""
        with get_session() as session:
            config = DataSourceConfig(
                source_code=data["source_code"],
                source_name=data["source_name"],
                layer=data.get("layer", "data_source"),
                market_categories=data.get("market_categories"),
                enabled=data.get("enabled", True),
                load_balance_strategy=data.get(
                    "load_balance_strategy", "round_robin"
                ),
                config_json=data.get("config_json"),
                dependencies=data.get("dependencies"),
                notes=data.get("notes"),
            )
            session.add(config)
            session.flush()
            result = self._to_dict(config)
            logger.info(f"Created data source config: {config.source_code}")
            return result

    def update_config(
        self, config_id: int, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """更新数据源配置"""
        with get_session() as session:
            config = session.query(DataSourceConfig).filter(
                DataSourceConfig.id == config_id
            ).first()
            if not config:
                return None

            allowed_fields = [
                "source_name", "layer", "market_categories", "enabled",
                "load_balance_strategy", "config_json", "dependencies", "notes"
            ]
            for field in allowed_fields:
                if field in data:
                    setattr(config, field, data[field])

            session.flush()
            logger.info(f"Updated data source config: {config.source_code}")
            return self._to_dict(config)

    def delete_config(self, config_id: int) -> bool:
        """删除数据源配置（级联删除关联的密钥和数据集）"""
        with get_session() as session:
            config = session.query(DataSourceConfig).filter(
                DataSourceConfig.id == config_id
            ).first()
            if not config:
                return False
            source_code = config.source_code
            session.delete(config)
            logger.info(f"Deleted data source config: {source_code}")
            return True

    def test_connection(self, config_id: int) -> Dict[str, Any]:
        """测试数据源连接"""
        config = self.get_config(config_id)
        if not config:
            return {"success": False, "message": "配置不存在"}

        source_code = config["source_code"]
        config_json = config.get("config_json") or {}

        try:
            if source_code.startswith("crypto_"):
                return self._test_crypto_connection(config, config_json)
            elif source_code.startswith("us_stock_"):
                return self._test_us_stock_connection(config, config_json)
            elif source_code.startswith("forex_"):
                return self._test_forex_connection(config, config_json)
            elif source_code.startswith("futures_"):
                return self._test_futures_connection(config, config_json)
            elif source_code.startswith("hk_stock_"):
                return self._test_hk_stock_connection(config, config_json)
            elif source_code.startswith("cn_stock_"):
                return self._test_cn_stock_connection(config, config_json)
            else:
                return {"success": True, "message": "通用配置，无需连接测试"}
        except Exception as e:
            logger.error(f"Connection test failed for {source_code}: {e}")
            return {"success": False, "message": f"连接测试失败: {str(e)}"}

    def _test_crypto_connection(self, config: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
        import ccxt
        exchange_id = cfg.get("default_exchange", "coinbase")
        if not hasattr(ccxt, exchange_id):
            return {"success": False, "message": f"交易所 {exchange_id} 不支持"}
        exchange = getattr(ccxt, exchange_id)({"enableRateLimit": True})
        exchange.load_markets()
        return {"success": True, "message": f"CCXT 交易所 {exchange_id} 连接正常"}

    def _test_us_stock_connection(self, config: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
        import requests
        base_url = cfg.get("base_url", "https://finnhub.io/api/v1")
        # Try a simple quote request
        resp = requests.get(
            f"{base_url}/quote",
            params={"symbol": "AAPL", "token": "demo"},
            timeout=10
        )
        if resp.status_code == 200:
            return {"success": True, "message": "Finnhub API 可达"}
        return {"success": False, "message": f"API 返回状态码 {resp.status_code}"}

    def _test_forex_connection(self, config: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
        import requests
        base_url = cfg.get("base_url", "https://api.twelvedata.com")
        resp = requests.get(f"{base_url}/time_series", timeout=10)
        # TwelveData returns 200 even for bad params, check if it's JSON
        try:
            resp.json()
            return {"success": True, "message": "TwelveData API 可达"}
        except Exception:
            return {"success": False, "message": "API 响应格式异常"}

    def _test_futures_connection(self, config: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
        return self._test_forex_connection(config, cfg)

    def _test_hk_stock_connection(self, config: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
        return self._test_forex_connection(config, cfg)

    def _test_cn_stock_connection(self, config: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import akshare
            akshare.stock_zh_a_spot_em()
            return {"success": True, "message": "AkShare 连接正常"}
        except Exception as e:
            return {"success": False, "message": f"AkShare 连接失败: {str(e)}"}

    def _to_dict(self, config: DataSourceConfig) -> Dict[str, Any]:
        return {
            "id": config.id,
            "source_code": config.source_code,
            "source_name": config.source_name,
            "layer": config.layer,
            "market_categories": config.market_categories,
            "enabled": config.enabled,
            "load_balance_strategy": config.load_balance_strategy,
            "config_json": config.config_json,
            "dependencies": config.dependencies,
            "notes": config.notes,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None,
        }


# Singleton
_data_source_service: Optional[DataSourceService] = None


def get_data_source_service() -> DataSourceService:
    global _data_source_service
    if _data_source_service is None:
        _data_source_service = DataSourceService()
    return _data_source_service
