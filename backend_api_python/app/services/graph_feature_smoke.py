"""Graph pipeline smoke checks."""
from typing import Any, Dict


class GraphFeatureSmoke:
    def run(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "imports": {},
            "repositories": {},
            "registered_collectors": [],
            "feature_writer": {},
        }

        try:
            from app.database.session import get_session
            from app.database.repositories.smoke import GraphOrmSmoke

            try:
                with get_session() as session:
                    result["repositories"] = GraphOrmSmoke(session).check_repositories()
            except Exception as e:
                result["repositories"] = {"error": str(e)}
            result["imports"]["db_smoke"] = True
        except Exception as e:
            result["imports"]["db_smoke"] = str(e)

        try:
            from app.collectors.scheduler import CollectorScheduler

            try:
                scheduler = CollectorScheduler()
                result["registered_collectors"] = scheduler.registry.names()
            except Exception as e:
                result["registered_collectors"] = [f"error:{e}"]
            result["imports"]["collector_scheduler"] = True
        except Exception as e:
            result["imports"]["collector_scheduler"] = str(e)

        try:
            from app.services.graph_feature_writer import GraphFeatureWriter

            writer = GraphFeatureWriter()
            result["feature_writer"] = {
                "build_daily_features": hasattr(writer, "build_daily_features"),
                "write_daily_features": hasattr(writer, "write_daily_features"),
                "write_company_narrative_features": hasattr(writer, "write_company_narrative_features"),
                "write_crypto_narrative_features": hasattr(writer, "write_crypto_narrative_features"),
                "write_polymarket_market_features": hasattr(writer, "write_polymarket_market_features"),
            }
            result["imports"]["feature_writer"] = True
        except Exception as e:
            result["imports"]["feature_writer"] = str(e)

        return result
