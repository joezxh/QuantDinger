"""
新闻数据模型
"""
from sqlalchemy import Column, BigInteger, String, Text, DateTime, DECIMAL, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import Base


class NewsArticle(Base):
    """新闻文章表"""
    __tablename__ = 'news_articles'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source = Column(String(100), nullable=False, comment='新闻来源')
    title = Column(String(500), nullable=False, comment='标题')
    content = Column(Text, comment='正文')
    summary = Column(Text, comment='摘要')
    url = Column(String(1000), unique=True, comment='原文链接')
    published_at = Column(DateTime(timezone=True), comment='发布时间')
    collected_at = Column(DateTime(timezone=True), default=datetime.utcnow, comment='采集时间')
    language = Column(String(10), default='en', comment='语言')
    author = Column(String(200), comment='作者')
    
    # 分类标签
    category = Column(String(50), comment='分类')
    tags = Column(ARRAY(String), comment='标签数组')
    
    # 关联标的
    related_symbols = Column(ARRAY(String), comment='相关标的')
    related_markets = Column(ARRAY(String(50)), comment='相关市场')
    
    # 情绪分析
    sentiment_score = Column(DECIMAL(6, 4), comment='情绪分数 (-1.0 ~ 1.0)')
    sentiment_label = Column(String(20), comment='bullish/bearish/neutral')
    importance_score = Column(DECIMAL(6, 4), default=0.5, comment='重要性分数')
    
    # Elasticsearch 同步状态
    es_synced = Column(String(20), default='pending', comment='pending/synced/failed')
    es_synced_at = Column(DateTime(timezone=True), comment='ES同步时间')
    
    # 元数据
    payload_json = Column(JSONB, comment='原始完整数据')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'source': self.source,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'url': self.url,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'collected_at': self.collected_at.isoformat() if self.collected_at else None,
            'language': self.language,
            'author': self.author,
            'category': self.category,
            'tags': self.tags,
            'related_symbols': self.related_symbols,
            'related_markets': self.related_markets,
            'sentiment_score': float(self.sentiment_score) if self.sentiment_score else None,
            'sentiment_label': self.sentiment_label,
            'importance_score': float(self.importance_score) if self.importance_score else None,
            'es_synced': self.es_synced,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
