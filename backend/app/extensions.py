'''QuantDinger Flask Extensions Module

This module initializes and provides access to all Flask extensions used by the application.
Currently includes Redis client for caching functionality.
'''

import os
import redis
from typing import Optional

# Redis client instance
def _get_redis_url() -> str:
    """Get Redis URL from environment variables."""
    host = os.getenv('REDIS_HOST', 'redis')
    port = os.getenv('REDIS_PORT', '6379')
    db = os.getenv('REDIS_DB', '0')
    password = os.getenv('REDIS_PASSWORD', None)
    
    if password:
        return f'redis://:{password}@{host}:{port}/{db}'
    else:
        return f'redis://{host}:{port}/{db}'

# Initialize Redis client
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'redis'),
        port=int(os.getenv('REDIS_PORT', '6379')),
        db=int(os.getenv('REDIS_DB', '0')),
        password=os.getenv('REDIS_PASSWORD', None),
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30
    )
    # Test the connection
    redis_client.ping()
except Exception as e:
    # Fallback to dummy client or raise appropriate error
    redis_client = None
    print(f'Warning: Redis connection failed: {e}')

# Other potential extensions can be added here
# For example:
# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy()

# from flask_migrate import Migrate
# migrate = Migrate()

# from flask_login import LoginManager
# login_manager = LoginManager()
