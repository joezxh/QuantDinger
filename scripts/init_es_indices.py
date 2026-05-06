"""
Elasticsearch 索引初始化脚本
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app
from app.services.elasticsearch_client import es_client


def init_es_indices():
    """初始化所有 Elasticsearch 索引"""
    app = create_app()
    
    with app.app_context():
        print("Initializing Elasticsearch indices...")
        es_client.init_indices()
        print("✓ Elasticsearch indices initialized successfully")
        
        # 验证索引创建
        indices = ['news_articles', 'security_companies', 'institution_entities', 'polymarket_users']
        for index in indices:
            exists = es_client.client.indices.exists(index=index)
            status = "✓" if exists else "✗"
            print(f"{status} Index '{index}': {'exists' if exists else 'NOT created'}")


if __name__ == '__main__':
    init_es_indices()
