"""数据库配置"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool
from pathlib import Path
from typing import Generator

from guax.core.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy 基类"""
    pass


# 创建数据库路径
db_path = Path(settings.database.url.replace("sqlite:///", ""))
db_path.parent.mkdir(parents=True, exist_ok=True)

# 创建引擎
if "sqlite" in settings.database.url:
    engine = create_engine(
        settings.database.url,
        echo=settings.database.echo,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
else:
    engine = create_engine(settings.database.url, echo=settings.database.echo)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库"""
    from guax.core.models import Media, ScraperSource, ScrapeTask
    Base.metadata.create_all(bind=engine)
