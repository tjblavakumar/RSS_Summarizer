from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import sessionmaker, relationship, DeclarativeBase
from datetime import datetime, timezone

class Base(DeclarativeBase):
    pass

class Feed(Base):
    __tablename__ = 'feeds'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    active = Column(Boolean, default=True)

class Topic(Base):
    __tablename__ = 'topics'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    keywords = Column(Text, nullable=False)
    active = Column(Boolean, default=True)

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False, unique=True)
    content = Column(Text)
    summary = Column(Text)
    author = Column(String(200))
    relevancy_score = Column(Integer)
    topic_scores = Column(JSON)
    feed_id = Column(Integer, ForeignKey('feeds.id'))
    topic_id = Column(Integer, ForeignKey('topics.id'))
    published_date = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    feed = relationship("Feed")
    topic = relationship("Topic")

# Database setup
engine = create_engine('sqlite:///news.db', connect_args={'check_same_thread': False})
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        pass