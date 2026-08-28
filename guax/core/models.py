"""媒体数据模型"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Text, DateTime, Boolean, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from guax.core.database import Base


class Media(Base):
    """媒体条目表"""
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 文件信息
    file_path: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    file_hash: Mapped[str] = mapped_column(String(64), index=True)
    
    # 元数据
    title: Mapped[str] = mapped_column(String(255), index=True)
    original_title: Mapped[str] = mapped_column(String(255), default="")
    studio: Mapped[str] = mapped_column(String(255), default="")
    studio_zh: Mapped[str] = mapped_column(String(255), default="")
    series: Mapped[str] = mapped_column(String(255), default="")
    director: Mapped[str] = mapped_column(String(255), default="")
    
    # 演员/标签
    actors: Mapped[str] = mapped_column(Text, default="")
    genres: Mapped[str] = mapped_column(String(500), default="")
    
    # 发行信息
    release_date: Mapped[str] = mapped_column(String(20), default="")
    year: Mapped[int] = mapped_column(Integer, default=0)
    runtime: Mapped[int] = mapped_column(Integer, default=0)
    
    # 评分
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    vote_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 简介
    plot: Mapped[str] = mapped_column(Text, default="")
    outline: Mapped[str] = mapped_column(Text, default="")
    
    # 封面和图片
    poster_path: Mapped[str] = mapped_column(String(500), default="")
    backdrop_path: Mapped[str] = mapped_column(String(500), default="")
    fanart_path: Mapped[str] = mapped_column(String(500), default="")
    
    # 刮削信息
    source: Mapped[str] = mapped_column(String(50), default="")
    source_id: Mapped[str] = mapped_column(String(255), default="")
    source_url: Mapped[str] = mapped_column(String(500), default="")
    scraped_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # 字幕
    has_subtitle: Mapped[bool] = mapped_column(Boolean, default=False)
    subtitle_language: Mapped[str] = mapped_column(String(20), default="")
    
    # 状态
    is_scrapped: Mapped[bool] = mapped_column(Boolean, default=False)
    is_nfo_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    tasks: Mapped[List["ScrapeTask"]] = relationship(back_populates="media", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Media(id={self.id}, title='{self.title}', source='{self.source}')>"


class ScraperSource(Base):
    """刮削源配置表"""
    __tablename__ = "scraper_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    config: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<ScraperSource(name='{self.name}', enabled={self.enabled})>"


class ScrapeTask(Base):
    """刮削任务表"""
    __tablename__ = "scrape_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    media_id: Mapped[int] = mapped_column(Integer, ForeignKey("media.id"), index=True)
    source: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    query: Mapped[str] = mapped_column(String(255), default="")
    result: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # 关系
    media: Mapped["Media"] = relationship(back_populates="tasks")

    def __repr__(self):
        return f"<ScrapeTask(id={self.id}, media_id={self.media_id}, status='{self.status}')>"


class ScrapeCache(Base):
    """刮削缓存表"""
    __tablename__ = "scrape_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cache_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(50))
    data: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ScrapeCache(key='{self.cache_key}', source='{self.source}')>"
