"""
宏观经济数据模型
"""
from sqlalchemy import Column, BigInteger, String, Text, DateTime, DECIMAL, ARRAY, Integer
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import Base


class MacroEconomicIndicator(Base):
    """宏观经济指标表"""
    __tablename__ = 'macro_economic_indicators'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 指标标识
    indicator_code = Column(String(100), nullable=False, comment='指标代码')
    indicator_name = Column(String(200), nullable=False, comment='指标名称')
    indicator_name_en = Column(String(200), comment='英文名称')
    
    # 分类
    category = Column(String(50), nullable=False, comment='分类 (gdp/labor/inflation/interest/trade)')
    sub_category = Column(String(50), comment='子分类')
    frequency = Column(String(20), comment='发布频率 (daily/weekly/monthly/quarterly/annually)')
    
    # 国家/地区
    country_code = Column(String(10), nullable=False, comment='国家代码 (US/CN/EU/JP)')
    country_name = Column(String(100), comment='国家名称')
    
    # 数值
    value = Column(DECIMAL(24, 8), comment='指标值')
    value_unit = Column(String(50), comment='单位')
    
    # 预期与历史
    forecast_value = Column(DECIMAL(24, 8), comment='预期值')
    previous_value = Column(DECIMAL(24, 8), comment='前值')
    revised_value = Column(DECIMAL(24, 8), comment='修正值')
    
    # 影响分析
    impact_level = Column(String(20), comment='影响等级 (high/medium/low)')
    impact_direction = Column(String(20), comment='影响方向 (bullish/bearish/neutral)')
    
    # 时间
    release_date = Column(DateTime(timezone=True), nullable=False, comment='发布日期')
    release_time = Column(String(20), comment='发布时间')
    period = Column(String(20), comment='数据周期 (2024-Q1)')
    
    # 来源
    source = Column(String(100), comment='数据来源')
    source_url = Column(String(1000), comment='来源链接')
    
    # ES 同步状态
    es_synced = Column(String(20), default='pending')
    es_synced_at = Column(DateTime(timezone=True))
    
    # 元数据
    payload_json = Column(JSONB, comment='原始完整数据')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        # 复合唯一索引：同一国家同一指标同一时间
        {'sqlite_autoincrement': True},
    )


class EconomicCalendarEvent(Base):
    """财经日历事件表"""
    __tablename__ = 'economic_calendar_events'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    event_name = Column(String(200), nullable=False, comment='事件名称')
    event_name_en = Column(String(200), comment='英文名称')
    country_code = Column(String(10), nullable=False)
    
    release_date = Column(DateTime(timezone=True), nullable=False)
    release_time = Column(String(20))
    
    importance = Column(String(20), comment='high/medium/low')
    
    actual_value = Column(String(50), comment='实际值（文本，可能带单位）')
    forecast_value = Column(String(50))
    previous_value = Column(String(50))
    
    impact_if_above = Column(String(20), comment='bullish/bearish')
    impact_if_below = Column(String(20))
    
    is_released = Column(String(20), default='pending', comment='pending/released')
    
    source = Column(String(100))
    
    es_synced = Column(String(20), default='pending')
    es_synced_at = Column(DateTime(timezone=True))
    
    payload_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
