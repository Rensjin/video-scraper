"""
刮削源管理器

统一管理所有刮削源，提供统一的搜索和刮削接口
"""
from typing import Optional, List, Dict, Any, Type
from loguru import logger

from guax.scrapers.base import ScraperBase, MediaMetadata
from guax.scrapers.javdb import JavdbScraper
from guax.scrapers.xht import XhtScraper
from guax.parsers.chinese_adult import FilenameParser, ParsedFilename


class ScraperManager:
    """刮削源管理器"""
    
    # 注册的刮削源
    _scrapers: Dict[str, ScraperBase] = {}
    
    # 文件名解析器
    _filename_parser: Optional[FilenameParser] = None
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._init_scrapers()
    
    def _init_scrapers(self):
        """初始化刮削源"""
        # 注册 JavDB
        javdb_config = self.config.get("javdb", {})
        self._scrapers["javdb"] = JavdbScraper(javdb_config)
        
        # 注册色花堂/1024
        xht_config = self.config.get("xht", {})
        self._scrapers["xht"] = XhtScraper(xht_config)
        
        # 初始化文件名解析器
        filename_config = self.config.get("filename_parser", {})
        self._filename_parser = FilenameParser(filename_config.get("custom_patterns", []))
        
        logger.info(f"已加载 {len(self._scrapers)} 个刮削源: {list(self._scrapers.keys())}")
    
    @property
    def filename_parser(self) -> FilenameParser:
        """获取文件名解析器"""
        return self._filename_parser
    
    def get_scraper(self, name: str) -> Optional[ScraperBase]:
        """获取刮削源"""
        return self._scrapers.get(name)
    
    def list_scrapers(self) -> List[Dict[str, Any]]:
        """列出所有刮削源"""
        return [
            {
                "name": s.name,
                "display_name": s.display_name,
                "priority": s.priority,
                "enabled": True,
            }
            for s in self._scrapers.values()
        ]
    
    async def scrape(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        prefer_source: Optional[str] = None,
        **kwargs
    ) -> Optional[MediaMetadata]:
        """
        刮削单个媒体
        
        Args:
            query: 搜索关键词
            sources: 指定刮削源列表，None 则使用全部
            prefer_source: 优先使用的刮削源
            
        Returns:
            媒体元数据
        """
        sources = sources or list(self._scrapers.keys())
        
        # 按优先级排序刮削源
        def get_priority(name: str) -> int:
            scraper = self._scrapers.get(name)
            if scraper:
                if name == prefer_source:
                    return -1  # 优先源最高优先级
                return scraper.priority
            return 999
        
        sorted_sources = sorted(sources, key=get_priority)
        
        last_error = None
        for source_name in sorted_sources:
            scraper = self._scrapers.get(source_name)
            if not scraper:
                continue
            
            try:
                logger.info(f"尝试使用 {scraper.display_name} 刮削: {query}")
                
                async with scraper:
                    results = await scraper.search(query, **kwargs)
                    
                    if results:
                        # 返回第一个结果
                        metadata = results[0]
                        
                        # 获取详情（如果需要）
                        if metadata.source_id and metadata.source_url:
                            detail = await scraper.get_detail(metadata.source_id)
                            if detail:
                                return detail
                        
                        return metadata
                        
            except Exception as e:
                logger.warning(f"{scraper.display_name} 刮削失败: {e}")
                last_error = e
                continue
        
        if last_error:
            logger.error(f"所有刮削源均失败: {last_error}")
        
        return None
    
    async def scrape_by_code(
        self,
        code: str,
        sources: Optional[List[str]] = None
    ) -> Optional[MediaMetadata]:
        """
        通过番号刮削
        
        Args:
            code: 番号（如 MD-001）
            sources: 指定刮削源
            
        Returns:
            媒体元数据
        """
        sources = sources or ["javdb"]  # 番号搜索优先用 JavDB
        
        for source_name in sources:
            scraper = self._scrapers.get(source_name)
            if not scraper:
                continue
            
            try:
                logger.info(f"通过番号 {code} 在 {scraper.display_name} 刮削")
                
                # 优先使用专门的番号搜索
                if hasattr(scraper, 'search_by_code'):
                    async with scraper:
                        metadata = await scraper.search_by_code(code)
                        if metadata:
                            return metadata
                
                # 回退到普通搜索
                async with scraper:
                    results = await scraper.search(code)
                    for result in results:
                        if result.source_code.upper() == code.upper():
                            # 获取详情
                            if hasattr(scraper, 'get_detail'):
                                return await scraper.get_detail(result.source_id)
                            return result
                            
            except Exception as e:
                logger.warning(f"{scraper.display_name} 番号刮削失败: {e}")
                continue
        
        return None
    
    def parse_filename(self, filename: str, file_path: Optional[str] = None) -> ParsedFilename:
        """
        解析文件名
        
        Args:
            filename: 文件名
            file_path: 完整路径
            
        Returns:
            解析结果
        """
        return self._filename_parser.parse(filename, file_path)
    
    async def scrape_from_file(
        self,
        file_path: str,
        sources: Optional[List[str]] = None,
        **kwargs
    ) -> Optional[MediaMetadata]:
        """
        从文件名自动解析并刮削
        
        Args:
            file_path: 文件完整路径
            sources: 指定刮削源
            
        Returns:
            媒体元数据
        """
        from pathlib import Path
        
        # 解析文件名
        parsed = self.parse_filename(Path(file_path).stem, file_path)
        
        logger.info(f"文件名解析: {parsed}")
        
        # 如果解析到番号，尝试番号搜索
        if parsed.code:
            metadata = await self.scrape_by_code(parsed.code, sources=sources)
            if metadata:
                return metadata
        
        # 如果有中文标题，尝试标题搜索
        if parsed.title_cn:
            metadata = await self.scrape(parsed.title_cn, sources=sources)
            if metadata:
                return metadata
        
        # 最后尝试原始文件名
        return await self.scrape(parsed.original, sources=sources)
    
    async def batch_scrape(
        self,
        queries: List[str],
        sources: Optional[List[str]] = None,
        **kwargs
    ) -> List[Optional[MediaMetadata]]:
        """
        批量刮削
        
        Args:
            queries: 搜索关键词列表
            sources: 指定刮削源
            
        Returns:
            媒体元数据列表
        """
        results = []
        for query in queries:
            metadata = await self.scrape(query, sources=sources, **kwargs)
            results.append(metadata)
        return results


# ===== 全局单例 =====
_scraper_manager: Optional[ScraperManager] = None


def get_scraper_manager(config: Optional[Dict[str, Any]] = None) -> ScraperManager:
    """获取刮削源管理器单例"""
    global _scraper_manager
    if _scraper_manager is None:
        _scraper_manager = ScraperManager(config)
    return _scraper_manager
