"""刮削源抽象基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import hashlib
import httpx
from loguru import logger


@dataclass
class MediaMetadata:
    """媒体元数据结构"""
    # 基础信息
    title: str = ""
    original_title: str = ""
    
    # 发行信息
    studio: str = ""
    studio_zh: str = ""
    series: str = ""
    director: str = ""
    
    # 演员/标签
    actors: List[str] = field(default_factory=list)
    genres: List[str] = field(default_factory=list)
    
    # 发行信息
    release_date: str = ""
    year: int = 0
    runtime: int = 0
    runtime_str: str = ""
    
    # 评分
    rating: float = 0.0
    rating_count: int = 0
    
    # 简介
    plot: str = ""
    outline: str = ""
    
    # 图片
    poster_url: str = ""
    backdrop_url: str = ""
    fanart_url: str = ""
    thumbnail_url: str = ""
    
    # 刮削源信息
    source_name: str = ""
    source_id: str = ""
    source_url: str = ""
    source_code: str = ""  # 番号/编号
    
    # 字幕
    subtitles: List[str] = field(default_factory=list)
    
    # 原始数据
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def title_zh(self) -> str:
        """获取中文标题"""
        return self.title
    
    @property
    def all_actors(self) -> str:
        """演员列表（逗号分隔）"""
        return ", ".join(self.actors)
    
    @property
    def all_genres(self) -> str:
        """类型列表（逗号分隔）"""
        return ", ".join(self.genres)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "original_title": self.original_title,
            "studio": self.studio,
            "studio_zh": self.studio_zh,
            "series": self.series,
            "director": self.director,
            "actors": self.actors,
            "genres": self.genres,
            "release_date": self.release_date,
            "year": self.year,
            "runtime": self.runtime,
            "rating": self.rating,
            "rating_count": self.rating_count,
            "plot": self.plot,
            "outline": self.outline,
            "poster_url": self.poster_url,
            "backdrop_url": self.backdrop_url,
            "fanart_url": self.fanart_url,
            "thumbnail_url": self.thumbnail_url,
            "source_name": self.source_name,
            "source_id": self.source_id,
            "source_url": self.source_url,
            "source_code": self.source_code,
            "subtitles": self.subtitles,
        }


class ScraperBase(ABC):
    """刮削源抽象基类"""
    
    name: str = ""  # 刮削源名称，如 "javdb", "xht"
    display_name: str = ""  # 显示名称
    priority: int = 100  # 优先级，数字越小越优先
    timeout: int = 30  # 超时时间（秒）
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.client:
            await self.client.aclose()
    
    @abstractmethod
    async def search(self, query: str, **kwargs) -> List[MediaMetadata]:
        """
        搜索媒体
        
        Args:
            query: 搜索关键词
            **kwargs: 其他参数
            
        Returns:
            搜索结果列表
        """
        pass
    
    @abstractmethod
    async def get_detail(self, media_id: str) -> Optional[MediaMetadata]:
        """
        获取详情
        
        Args:
            media_id: 媒体 ID
            
        Returns:
            媒体元数据
        """
        pass
    
    async def download_image(self, url: str, save_path: Path) -> bool:
        """
        下载图片
        
        Args:
            url: 图片 URL
            save_path: 保存路径
            
        Returns:
            是否成功
        """
        if not url or not self.client:
            return False
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            response = await self.client.get(url)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            logger.error(f"下载图片失败: {url}, error: {e}")
            return False
    
    @staticmethod
    def hash_string(s: str) -> str:
        """计算字符串的 MD5 哈希"""
        return hashlib.md5(s.encode()).hexdigest()
    
    @staticmethod
    def parse_date(date_str: str) -> tuple:
        """
        解析日期字符串
        
        Returns:
            (year, date_str)
        """
        if not date_str:
            return 0, ""
        
        import re
        year_match = re.search(r'\d{4}', date_str)
        if year_match:
            year = int(year_match.group())
            return year, date_str
        return 0, date_str
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        # 移除多余空白
        text = " ".join(text.split())
        return text.strip()
    
    def log(self, level: str, message: str):
        """日志记录"""
        getattr(logger, level)(f"[{self.name}] {message}")
