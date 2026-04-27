"""Indicator community repository."""
from sqlalchemy import select, desc, func

from app.database.repositories.base import BaseRepository
from app.models.indicator_full import IndicatorCode, IndicatorComment, IndicatorPurchase


class IndicatorRepository(BaseRepository):
    def get_by_id(self, indicator_id: int):
        return self.session.get(IndicatorCode, indicator_id)

    def list_by_user(self, user_id: int, limit: int = 20, offset: int = 0):
        stmt = (
            select(IndicatorCode)
            .where(IndicatorCode.user_id == user_id)
            .order_by(desc(IndicatorCode.id))
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def list_community(self, limit: int = 20, offset: int = 0):
        stmt = (
            select(IndicatorCode)
            .where(
                IndicatorCode.publish_to_community == 1,
                IndicatorCode.review_status == "approved",
            )
            .order_by(desc(IndicatorCode.purchase_count))
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def create_indicator(self, **kwargs):
        indicator = IndicatorCode(**kwargs)
        self.add(indicator)
        self.flush()
        return indicator

    def update_indicator(self, indicator_id: int, **kwargs):
        indicator = self.get_by_id(indicator_id)
        if indicator:
            for k, v in kwargs.items():
                setattr(indicator, k, v)
            self.flush()
        return indicator

    def increment_purchase_count(self, indicator_id: int):
        indicator = self.get_by_id(indicator_id)
        if indicator:
            indicator.purchase_count = (indicator.purchase_count or 0) + 1
            self.flush()
        return indicator

    def get_purchase(self, indicator_id: int, buyer_id: int):
        stmt = (
            select(IndicatorPurchase)
            .where(
                IndicatorPurchase.indicator_id == indicator_id,
                IndicatorPurchase.buyer_id == buyer_id,
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_purchase(self, **kwargs):
        purchase = IndicatorPurchase(**kwargs)
        self.add(purchase)
        self.flush()
        return purchase

    def list_comments(self, indicator_id: int, limit: int = 50):
        stmt = (
            select(IndicatorComment)
            .where(
                IndicatorComment.indicator_id == indicator_id,
                IndicatorComment.is_deleted == 0,
            )
            .order_by(desc(IndicatorComment.created_at))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def create_comment(self, **kwargs):
        comment = IndicatorComment(**kwargs)
        self.add(comment)
        self.flush()
        return comment

    def get_avg_rating(self, indicator_id: int) -> float:
        stmt = select(func.avg(IndicatorComment.rating)).where(
            IndicatorComment.indicator_id == indicator_id,
            IndicatorComment.is_deleted == 0,
        )
        result = self.session.execute(stmt).scalar()
        return float(result) if result else 0.0

    def delete_indicator(self, indicator_id: int, user_id: int) -> bool:
        indicator = self.get_by_id(indicator_id)
        if indicator and indicator.user_id == user_id and (indicator.is_buy is None or indicator.is_buy == 0):
            self.session.delete(indicator)
            self.flush()
            return True
        return False

    def get_indicator_for_edit(self, indicator_id: int, user_id: int):
        """Get indicator if owned by user and not a purchased copy."""
        stmt = (
            select(IndicatorCode)
            .where(
                IndicatorCode.id == indicator_id,
                IndicatorCode.user_id == user_id,
            )
        )
        indicator = self.session.execute(stmt).scalar_one_or_none()
        if indicator and indicator.is_buy == 1:
            return None  # Purchased indicators are read-only
        return indicator

    def get_indicator_for_call(self, indicator_ref, user_id: int):
        """Get indicator code by ID or name with permission check.

        For int ID: returns indicator if owned by user or published to community.
        For str name: returns indicator matching name (own first, then community).
        Returns (code, indicator_id) or (None, None).
        """
        if isinstance(indicator_ref, int):
            stmt = (
                select(IndicatorCode)
                .where(
                    IndicatorCode.id == indicator_ref,
                    (IndicatorCode.user_id == user_id) | (IndicatorCode.publish_to_community == 1),
                )
            )
            indicator = self.session.execute(stmt).scalar_one_or_none()
            if indicator:
                return indicator.code, indicator.id
            return None, None

        # By name: own first, then community
        name = str(indicator_ref)
        stmt = (
            select(IndicatorCode)
            .where(
                IndicatorCode.name == name,
                IndicatorCode.user_id == user_id,
            )
        )
        indicator = self.session.execute(stmt).scalar_one_or_none()
        if indicator:
            return indicator.code, indicator.id

        stmt = (
            select(IndicatorCode)
            .where(
                IndicatorCode.name == name,
                IndicatorCode.publish_to_community == 1,
            )
        )
        indicator = self.session.execute(stmt).scalar_one_or_none()
        if indicator:
            return indicator.code, indicator.id
        return None, None

    def get_code_by_id(self, indicator_id: int):
        """Get raw code for an indicator by ID (no permission check)."""
        indicator = self.get_by_id(indicator_id)
        return indicator.code if indicator else None
