from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from config.database import Base
from sqlalchemy import Index

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    phone = Column(String(20))
    location = Column(String(255))
    language = Column(String(10), default='uz')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Listing(Base):
    __tablename__ = "listings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    title = Column(String(255))
    description = Column(Text)
    rooms = Column(Integer)
    floor = Column(Integer)
    total_floors = Column(Integer)
    price = Column(Integer)
    currency = Column(String(10), default='USD')
    images = Column(Text)  # JSON string of image file_ids
    location = Column(String(255))  # "latitude,longitude" format
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))

# Indexlar klasslardan keyin bo'lishi kerak
Index('idx_user_telegram_id', User.telegram_id)
Index('idx_listing_user_id', Listing.user_id)
Index('idx_listing_active', Listing.is_active)
Index('idx_listing_created', Listing.created_at)