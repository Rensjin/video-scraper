"""JavDB 刮削源

JavDB 是一个知名的日本成人视频数据库，也收录了不少国产视频
站点: https://javdb.com
"""
import re
import json
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode, quote
from bs4 import BeautifulSoup
from loguru import logger

from guax.scrapers.base import ScraperBase, MediaMetadata


class JavdbScraper(ScraperBase):
    """JavDB 刮削源"""
    
    name = "javdb"
    display_name = "JavDB"
    priority = 10  # 高优先级
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = self.config.get("base_url", "https://javdb.com")
        self.timeout = self.config.get("timeout", 30)
    
    async def search(self, query: str, **kwargs) -> List[MediaMetadata]:
        """
        搜索媒体
        
        Args:
            query: 搜索关键词（可以是番号或标题）
            
        Returns:
            搜索结果列表
        """
        results = []
        
        try:
            # 编码搜索关键词
            encoded_query = quote(query)
            search_url = f"{self.base_url}/search?q={encoded_query}&f=all"
            
            self.log("info", f"搜索: {search_url}")
            
            response = await self.client.get(search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 解析搜索结果
            items = soup.select('div.movie-list div.item')
            
            for item in items[:10]:  # 最多返回10个结果
                try:
                    metadata = self._parse_search_item(item)
                    if metadata:
                        results.append(metadata)
                except Exception as e:
                    self.log("warning", f"解析搜索项失败: {e}")
                    continue
            
            self.log("info", f"搜索到 {len(results)} 个结果")
            
        except Exception as e:
            self.log("error", f"搜索失败: {e}")
        
        return results
    
    async def get_detail(self, media_id: str) -> Optional[MediaMetadata]:
        """
        获取详情
        
        Args:
            media_id: 媒体 ID（JavDB 的 UID 或番号）
            
        Returns:
            媒体元数据
        """
        try:
            # 尝试直接作为番号访问
            detail_url = f"{self.base_url}/v/{media_id}"
            
            self.log("info", f"获取详情: {detail_url}")
            
            response = await self.client.get(detail_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            return self._parse_detail_page(soup, detail_url)
            
        except Exception as e:
            self.log("error", f"获取详情失败: {e}")
            return None
    
    async def search_by_code(self, code: str) -> Optional[MediaMetadata]:
        """
        通过番号搜索
        
        Args:
            code: 番号（如 MD-001, SWAG-001）
            
        Returns:
            媒体元数据
        """
        try:
            # JavDB 的番号搜索 URL
            search_url = f"{self.base_url}/search?q={quote(code)}&f=all"
            
            self.log("info", f"番号搜索: {search_url}")
            
            response = await self.client.get(search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 查找匹配的番号
            items = soup.select('div.movie-list div.item')
            
            for item in items[:5]:
                # 检查番号是否匹配
                code_element = item.select_one('span.uid')
                if code_element:
                    item_code = code_element.get_text(strip=True)
                    if code.upper() == item_code.upper():
                        # 找到匹配，解析详情
                        link = item.select_one('a')
                        if link:
                            detail_url = self.base_url + link.get('href')
                            return await self.get_detail_by_url(detail_url)
            
            self.log("info", f"番号 {code} 未找到")
            return None
            
        except Exception as e:
            self.log("error", f"番号搜索失败: {e}")
            return None
    
    async def get_detail_by_url(self, url: str) -> Optional[MediaMetadata]:
        """
        通过 URL 获取详情
        
        Args:
            url: 详情页 URL
            
        Returns:
            媒体元数据
        """
        try:
            self.log("info", f"获取详情: {url}")
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            return self._parse_detail_page(soup, url)
            
        except Exception as e:
            self.log("error", f"获取详情失败: {e}")
            return None
    
    def _parse_search_item(self, item) -> Optional[MediaMetadata]:
        """解析搜索列表项"""
        try:
            # 获取链接和标题
            link = item.select_one('a')
            if not link:
                return None
            
            title = link.get('title', '')
            detail_url = self.base_url + link.get('href', '')
            
            # 获取番号
            code_elem = item.select_one('span.uid')
            code = code_elem.get_text(strip=True) if code_elem else ''
            
            # 获取封面图
            img = item.select_one('img')
            poster_url = img.get('src', '') if img else ''
            
            # 获取评分
            rating = 0.0
            rating_elem = item.select_one('span.value')
            if rating_elem:
                try:
                    rating = float(rating_elem.get_text(strip=True))
                except:
                    pass
            
            if not title:
                return None
            
            metadata = MediaMetadata(
                title=title,
                source_code=code,
                source_id=code,
                source_url=detail_url,
                source_name=self.name,
                poster_url=poster_url,
                rating=rating,
                raw_data={'url': detail_url}
            )
            
            return metadata
            
        except Exception as e:
            self.log("warning", f"解析搜索项失败: {e}")
            return None
    
    def _parse_detail_page(self, soup: BeautifulSoup, url: str) -> Optional[MediaMetadata]:
        """解析详情页"""
        try:
            # 获取标题
            title_elem = soup.select_one('h2.title')
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # 获取番号
            code_elem = soup.select_one('span.uid')
            code = code_elem.get_text(strip=True) if code_elem else ''
            
            # 获取封面
            poster_url = ''
            cover_section = soup.select_one('section.cover')
            if cover_section:
                img = cover_section.select_one('img')
                poster_url = img.get('src', '') if img else ''
            
            # 获取预览图
            preview_images = []
            gallery = soup.select('div.thumbnail-columns a')
            for a in gallery:
                img = a.select_one('img')
                if img:
                    src = img.get('src', '') or img.get('data-src', '')
                    if src:
                        preview_images.append(src)
            
            # 获取评分
            rating = 0.0
            rating_elem = soup.select_one('span.score')
            if rating_elem:
                try:
                    rating_text = rating_elem.get_text(strip=True)
                    rating = float(rating_text)
                except:
                    pass
            
            # 获取导演
            director = ''
            director_section = soup.select_one('div.panel:has(span:contains("导演"))')
            if director_section:
                director_link = director_section.select_one('a')
                director = director_link.get_text(strip=True) if director_link else ''
            
            # 获取发行日期
            release_date = ''
            date_section = soup.select_one('div.panel:has(span:contains("日期"))')
            if date_section:
                date_text = date_section.get_text(strip=True)
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
                if date_match:
                    release_date = date_match.group(1)
            
            # 获取时长
            runtime = 0
            runtime_section = soup.select_one('div.panel:has(span:contains("时长"))')
            if runtime_section:
                runtime_text = runtime_section.get_text(strip=True)
                runtime_match = re.search(r'(\d+)', runtime_text)
                if runtime_match:
                    runtime = int(runtime_match.group(1))
            
            # 获取片商
            studio = ''
            studio_section = soup.select_one('div.panel:has(span:contains("片商"))')
            if studio_section:
                studio_link = studio_section.select_one('a')
                studio = studio_link.get_text(strip=True) if studio_link else ''
            
            # 获取系列
            series = ''
            series_section = soup.select_one('div.panel:has(span:contains("系列"))')
            if series_section:
                series_link = series_section.select_one('a')
                series = series_link.get_text(strip=True) if series_link else ''
            
            # 获取演员
            actors = []
            actor_section = soup.select_one('div.panel:has(span:contains("演员"))')
            if actor_section:
                actor_links = actor_section.select('a')
                actors = [a.get_text(strip=True) for a in actor_links]
            
            # 获取类型/标签
            genres = []
            genre_section = soup.select_one('div.movie-tags')
            if genre_section:
                genre_links = genre_section.select('a')
                genres = [a.get_text(strip=True) for a in genre_links]
            
            # 获取简介
            plot = ''
            plot_section = soup.select_one('div.movie-synopsis')
            if plot_section:
                plot = plot_section.get_text(strip=True)
            
            # 解析年份
            year = 0
            if release_date:
                year_match = re.search(r'(\d{4})', release_date)
                if year_match:
                    year = int(year_match.group(1))
            
            metadata = MediaMetadata(
                title=title,
                original_title=title,
                source_code=code,
                source_id=code,
                source_url=url,
                source_name=self.name,
                poster_url=poster_url,
                backdrop_url=preview_images[0] if preview_images else '',
                fanart_url=preview_images[0] if preview_images else '',
                thumbnail_url=preview_images[0] if preview_images else '',
                rating=rating,
                director=director,
                studio=studio,
                series=series,
                actors=actors,
                genres=genres,
                release_date=release_date,
                year=year,
                runtime=runtime,
                runtime_str=f"{runtime}分钟" if runtime else "",
                plot=plot,
                outline=plot[:200] if plot else '',
                raw_data={
                    'url': url,
                    'preview_images': preview_images
                }
            )
            
            return metadata
            
        except Exception as e:
            self.log("error", f"解析详情页失败: {e}")
            return None


# ===== 导出 =====
__all__ = ['JavdbScraper']
