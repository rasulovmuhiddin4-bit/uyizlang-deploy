from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import os

# Production uchun connection pool
engine = create_engine(
    os.getenv('DATABASE_URL', 'sqlite:///bot.db'),
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600
)