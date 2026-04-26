"""
数据集元数据服务
管理 DataSourceDataset 的 CRUD 操作
"""
from typing import Optional, Dict, Any, List

from app.database.session import get_session
from app.models.data_source_meta import DataSourceDataset
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DatasetService:
    """数据集元数据服务"""

    def list_datasets(
        self,
        source_id: Optional[int] = None,
        dataset_code: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """列出数据集元数据"""
        with get_session() as session:
            query = session.query(DataSourceDataset)

            if source_id:
                query = query.filter(DataSourceDataset.source_id == source_id)
            if dataset_code:
                query = query.filter(DataSourceDataset.dataset_code == dataset_code)
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    (DataSourceDataset.dataset_code.ilike(search_pattern)) |
                    (DataSourceDataset.dataset_name.ilike(search_pattern))
                )

            total = query.count()
            items = query.order_by(DataSourceDataset.id).offset(
                (page - 1) * page_size
            ).limit(page_size).all()

            return {
                "items": [self._to_dict(item) for item in items],
                "total": total,
                "page": page,
                "page_size": page_size
            }

    def get_dataset(self, dataset_id: int) -> Optional[Dict[str, Any]]:
        """获取单个数据集"""
        with get_session() as session:
            dataset = session.query(DataSourceDataset).filter(
                DataSourceDataset.id == dataset_id
            ).first()
            return self._to_dict(dataset) if dataset else None

    def get_dataset_by_code(self, dataset_code: str) -> Optional[Dict[str, Any]]:
        """通过 dataset_code 获取数据集"""
        with get_session() as session:
            dataset = session.query(DataSourceDataset).filter(
                DataSourceDataset.dataset_code == dataset_code
            ).first()
            return self._to_dict(dataset) if dataset else None

    def create_dataset(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建数据集"""
        with get_session() as session:
            dataset = DataSourceDataset(
                source_id=data["source_id"],
                dataset_code=data["dataset_code"],
                dataset_name=data["dataset_name"],
                description=data.get("description"),
                function_name=data.get("function_name"),
                return_type=data.get("return_type", "list[dict]"),
                fields_schema=data.get("fields_schema"),
                sample_output=data.get("sample_output"),
                coverage_text=data.get("coverage_text"),
                source_file_ref=data.get("source_file_ref"),
            )
            session.add(dataset)
            session.flush()
            logger.info(f"Created dataset: {dataset.dataset_code}")
            return self._to_dict(dataset)

    def update_dataset(self, dataset_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新数据集"""
        with get_session() as session:
            dataset = session.query(DataSourceDataset).filter(
                DataSourceDataset.id == dataset_id
            ).first()
            if not dataset:
                return None

            allowed_fields = [
                "dataset_name", "description", "function_name", "return_type",
                "fields_schema", "sample_output", "coverage_text", "source_file_ref"
            ]
            for field in allowed_fields:
                if field in data:
                    setattr(dataset, field, data[field])

            session.flush()
            logger.info(f"Updated dataset: {dataset.dataset_code}")
            return self._to_dict(dataset)

    def delete_dataset(self, dataset_id: int) -> bool:
        """删除数据集"""
        with get_session() as session:
            dataset = session.query(DataSourceDataset).filter(
                DataSourceDataset.id == dataset_id
            ).first()
            if not dataset:
                return False
            code = dataset.dataset_code
            session.delete(dataset)
            logger.info(f"Deleted dataset: {code}")
            return True

    def get_datasets_by_source(self, source_id: int) -> List[Dict[str, Any]]:
        """获取某个数据源下的所有数据集"""
        with get_session() as session:
            items = session.query(DataSourceDataset).filter(
                DataSourceDataset.source_id == source_id
            ).order_by(DataSourceDataset.id).all()
            return [self._to_dict(item) for item in items]

    def _to_dict(self, dataset: DataSourceDataset) -> Dict[str, Any]:
        return {
            "id": dataset.id,
            "source_id": dataset.source_id,
            "dataset_code": dataset.dataset_code,
            "dataset_name": dataset.dataset_name,
            "description": dataset.description,
            "function_name": dataset.function_name,
            "return_type": dataset.return_type,
            "fields_schema": dataset.fields_schema,
            "sample_output": dataset.sample_output,
            "coverage_text": dataset.coverage_text,
            "source_file_ref": dataset.source_file_ref,
            "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
            "updated_at": dataset.updated_at.isoformat() if dataset.updated_at else None,
        }


# Singleton
_dataset_service: Optional[DatasetService] = None


def get_dataset_service() -> DatasetService:
    global _dataset_service
    if _dataset_service is None:
        _dataset_service = DatasetService()
    return _dataset_service
