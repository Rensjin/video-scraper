"""配置管理"""
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, List
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    name: str = "Guax"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    language: str = "zh_CN"


class DatabaseConfig(BaseModel):
    url: str = "sqlite:///data/guax.db"
    echo: bool = False


class MediaConfig(BaseModel):
    """媒体库配置"""
    base_path: str = "./media"
    nfo_template: str = "kodi"
    poster_suffix: str = "-poster.jpg"
    backdrop_suffix: str = "-backdrop.jpg"
    fanart_suffix: str = "-fanart.jpg"
    output_structure: str = "{title}/"


class ScraperConfig(BaseModel):
    """刮削器配置"""
    enabled_sources: List[str] = ["filename", "javdb", "xht"]
    timeout: int = 30
    retry_times: int = 3
    cache_ttl: int = 86400 * 7  # 7天缓存


class FilenameParserConfig(BaseModel):
    """文件名解析器配置"""
    enabled_patterns: List[str] = [
        "md", "mdb", "swag", "91", "xs", "sq", "sg", "nnuu", "heyzo", "tokyo-hot"
    ]
    custom_patterns: List[dict] = []


class JavdbConfig(BaseModel):
    """JavDB 配置"""
    base_url: str = "https://javdb.com"
    timeout: int = 30
    proxies: Optional[str] = None


class XhtConfig(BaseModel):
    """色花堂配置"""
    base_url: str = "https://xinghuaren.com"
    timeout: int = 30
    proxies: Optional[str] = None


class Settings(BaseModel):
    """全局配置"""
    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    media: MediaConfig = Field(default_factory=MediaConfig)
    scraper: ScraperConfig = Field(default_factory=ScraperConfig)
    filename_parser: FilenameParserConfig = Field(default_factory=FilenameParserConfig)
    javdb: JavdbConfig = Field(default_factory=JavdbConfig)
    xht: XhtConfig = Field(default_factory=XhtConfig)


def load_config(config_path: str = "config/config.yaml") -> Settings:
    """加载配置文件"""
    path = Path(config_path)
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        return Settings(**data)
    return Settings()


# 全局配置实例
settings = load_config()
