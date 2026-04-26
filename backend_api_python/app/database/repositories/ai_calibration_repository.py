"""AI calibration repository."""
from datetime import date

from sqlalchemy import desc, select

from app.database.repositories.base import BaseRepository
from app.models.analysis import AiCalibration


class AiCalibrationRepository(BaseRepository):
    def get_latest(self, market: str):
        """Get latest calibration record for a market."""
        stmt = (
            select(AiCalibration)
            .where(AiCalibration.market == market)
            .order_by(desc(AiCalibration.validated_at))
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_calibration(self, **kwargs):
        """Insert a new calibration record."""
        record = AiCalibration(**kwargs)
        self.add(record)
        self.flush()
        return record
