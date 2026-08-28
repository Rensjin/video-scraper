"""XHT 数据源

XHT 是一个知名的华语视频分享站

这类站点的特点：
- 标题包含丰富的元信息（片商、演员、时长等）
- 使用中文描述
- 发布格式相对统一
"""
import re
from typing import Optional, List, Dict, Any
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
from loguru import logger

from guax.scrapers.base import ScraperBase, MediaMetadata


class XhtScraper(ScraperBase):
    """XHT 数据源"""
    
    name = "xht"
    display_name = "XHT"
    priority = 20  # 次优先级
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = self.config.get("base_url", "https://xinghuaren.com")
        self.timeout = self.config.get("timeout", 30)
        
        # 常见的 1024 系域名
        self.mirror_urls = [
            "https://xinghuaren.com",
            "https://t66y.com",  # 1024
            "https://91shenqi.com",
        ]
    
    async def search(self, query: str, **kwargs) -> List[MediaMetadata]:
        """
        搜索媒体
        
        Args:
            query: 搜索关键词
            
        Returns:
            搜索结果列表
        """
        results = []
        
        try:
            # 编码搜索关键词
            encoded_query = quote(query)
            
            # 尝试在不同镜像站搜索
            for base in [self.base_url] + self.mirror_urls:
                try:
                    # 通用搜索 URL 格式
                    search_paths = [
                        f"/search.php?kw={encoded_query}",
                        f"/search/{encoded_query}",
                        f"/?search={encoded_query}",
                    ]
                    
                    for path in search_paths:
                        try:
                            search_url = urljoin(base, path)
                            response = await self.client.get(search_url, timeout=10)
                            if response.status_code == 200:
                                results = await self._parse_search_results(response.text, base)
                                if results:
                                    self.log("info", f"在 {base} 搜索到 {len(results)} 个结果")
                                    return results
                        except Exception:
                            continue
                            
                except Exception as e:
                    self.log("warning", f"搜索 {base} 失败: {e}")
                    continue
            
            self.log("info", f"搜索到 {len(results)} 个结果")
            
        except Exception as e:
            self.log("error", f"搜索失败: {e}")
        
        return results
    
    async def get_detail(self, media_id: str) -> Optional[MediaMetadata]:
        """
        获取详情
        
        Args:
            media_id: 媒体 ID
            
        Returns:
            媒体元数据
        """
        try:
            # 尝试作为 URL 或 ID 处理
            if media_id.startswith('http'):
                url = media_id
            else:
                url = urljoin(self.base_url, f"/thread/{media_id}")
            
            self.log("info", f"获取详情: {url}")
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            return self._parse_detail_page(soup, url)
            
        except Exception as e:
            self.log("error", f"获取详情失败: {e}")
            return None
    
    async def parse_thread_content(self, title: str, content: str, url: str = "") -> Optional[MediaMetadata]:
        """
        从帖子标题和内容解析元数据
        
        这是 1024 系站点的主要使用场景：
        - 输入帖子的标题和内容
        - 自动解析出片商、演员、时长等信息
        
        Args:
            title: 帖子标题
            content: 帖子内容（包含图片描述等）
            url: 帖子链接
            
        Returns:
            媒体元数据
        """
        try:
            metadata = MediaMetadata(
                source_name=self.name,
                source_url=url,
            )
            
            # 解析标题
            title = title.strip()
            metadata.title = title
            
            # 提取番号
            code = self._extract_code_from_text(title)
            if code:
                metadata.source_code = code
                metadata.source_id = code
            
            # 提取片商
            studio = self._extract_studio_from_text(title, content)
            if studio:
                metadata.studio_zh = studio
                metadata.studio = studio
            
            # 提取演员
            actors = self._extract_actors_from_text(title, content)
            if actors:
                metadata.actors = actors
            
            # 提取时长
            runtime = self._extract_runtime_from_text(title, content)
            if runtime:
                metadata.runtime = runtime
                metadata.runtime_str = f"{runtime}分钟"
            
            # 提取年份
            year = self._extract_year_from_text(title, content)
            if year:
                metadata.year = year
                metadata.release_date = str(year)
            
            # 提取类型/标签
            genres = self._extract_genres_from_text(title, content)
            if genres:
                metadata.genres = genres
            
            # 提取简介
            plot = self._extract_plot_from_text(content)
            if plot:
                metadata.plot = plot
                metadata.outline = plot[:200]
            
            # 提取图片
            images = self._extract_images_from_text(content)
            if images:
                metadata.poster_url = images[0] if len(images) > 0 else ""
                metadata.thumbnail_url = images[0] if len(images) > 0 else ""
                metadata.fanart_url = images[0] if len(images) > 0 else ""
            
            return metadata
            
        except Exception as e:
            self.log("error", f"解析帖子内容失败: {e}")
            return None
    
    def _parse_search_results(self, html: str, base_url: str) -> List[MediaMetadata]:
        """解析搜索结果页面"""
        results = []
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # 1024 系常见的列表样式
            items = soup.select('tr.tr2, div.thread-item, li.topic-item, div.item')
            
            for item in items[:20]:
                try:
                    # 尝试提取标题和链接
                    link = item.select_one('a')
                    if not link:
                        continue
                    
                    title = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    if not title or not href:
                        continue
                    
                    # 完整 URL
                    if not href.startswith('http'):
                        href = urljoin(base_url, href)
                    
                    # 提取番号
                    code = self._extract_code_from_text(title)
                    
                    metadata = MediaMetadata(
                        title=title,
                        source_code=code or "",
                        source_id=code or href,
                        source_url=href,
                        source_name=self.name,
                    )
                    
                    results.append(metadata)
                    
                except Exception as e:
                    self.log("warning", f"解析搜索项失败: {e}")
                    continue
                    
        except Exception as e:
            self.log("error", f"解析搜索结果失败: {e}")
        
        return results
    
    def _parse_detail_page(self, soup: BeautifulSoup, url: str) -> Optional[MediaMetadata]:
        """解析详情页"""
        try:
            metadata = MediaMetadata(
                source_name=self.name,
                source_url=url,
            )
            
            # 获取标题
            title_elem = soup.select_one('h1, h2.title, .thread-title')
            if title_elem:
                metadata.title = title_elem.get_text(strip=True)
            
            # 提取番号
            if metadata.title:
                code = self._extract_code_from_text(metadata.title)
                if code:
                    metadata.source_code = code
                    metadata.source_id = code
            
            # 获取内容
            content_elem = soup.select_one('div.content, div.post-content, .tpc_content')
            if content_elem:
                content = content_elem.get_text(separator='\n', strip=True)
                metadata.plot = content[:500]
                metadata.outline = content[:200]
                
                # 提取更多信息
                metadata.actors = self._extract_actors_from_text(metadata.title, content)
                metadata.studio_zh = self._extract_studio_from_text(metadata.title, content)
                metadata.genres = self._extract_genres_from_text(metadata.title, content)
            
            # 提取图片
            images = []
            if content_elem:
                for img in content_elem.select('img'):
                    src = img.get('src') or img.get('data-src')
                    if src and not src.endswith('.gif'):
                        images.append(src)
            
            if images:
                metadata.poster_url = images[0]
                metadata.thumbnail_url = images[0]
            
            return metadata
            
        except Exception as e:
            self.log("error", f"解析详情页失败: {e}")
            return None
    
    def _extract_code_from_text(self, text: str) -> str:
        """从文本中提取番号"""
        # 常见番号模式
        patterns = [
            # 标准日文番号: ABC-123, ABCD-1234
            r'([A-Z]{2,6}[-_\s]?\d{2,5})',
            # 国产番号: MD-001, SWAG-001, 91xxx
            r'(MD[-_\s]?\d+)',
            r'(SWAG[-_\s]?\d+)',
            r'(91[_-]?\w+)',
            r'(MDB[-_\s]?\d+)',
            r'(XS[-_\s]?\d+)',
            r'(NnUU[-_\s]?\d+)',
            # 无码系列
            r'(N0101[-_\s]?\d+)',
            r'(CARIB[-_\s]?\d+)',
            # 10mu/1Pondo
            r'(10MU[-_\s]?\d+)',
            r'(1P[-_\s]?\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(1)
                # 规范化格式
                code = re.sub(r'[-_\s]', '-', code)
                return code.upper()
        
        return ""
    
    def _extract_studio_from_text(self, title: str, content: str) -> str:
        """从文本中提取片商"""
        text = title + " " + content
        
        # 常见的国产片商
        studios = [
            "麻豆传媒", "SWAG", "91原创", "台湾swag", "台湾SWAG",
            "深爱网", "我爱肉", "诱人的你", "香艳社区",
            "色花堂", "含羞草", "美尻", "翘臀",
            "国产剧情", "国产偷拍", "国产自拍", "国产原创",
        ]
        
        for studio in studios:
            if studio in text:
                return studio
        
        # 尝试从标题提取
        # 格式: [片商名] 标题 或 片商名-标题
        match = re.search(r'\[([^\]]+)\]', title)
        if match:
            return match.group(1)
        
        match = re.search(r'^([^\s\[\]]+)[-\s]', title)
        if match:
            potential = match.group(1)
            if len(potential) >= 2 and len(potential) <= 10:
                return potential
        
        return ""
    
    def _extract_actors_from_text(self, title: str, content: str) -> List[str]:
        """从文本中提取演员"""
        actors = []
        text = title + " " + content
        
        # 常见演员提取模式
        patterns = [
            # [演员名]
            r'\[([^\]]+)\]',
            # @演员名
            r'@(\w+)',
            # 演员：xxx
            r'演员[：:]\s*([^\s，,。]+)',
            # 主演：xxx
            r'主演[：:]\s*([^\s，,。]+)',
            # 女优：xxx
            r'女优[：:]\s*([^\s，,。]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                name = match.strip()
                if len(name) >= 2 and len(name) <= 10 and name not in actors:
                    actors.append(name)
        
        return actors
    
    def _extract_runtime_from_text(self, title: str, content: str) -> int:
        """从文本中提取时长（分钟）"""
        text = title + " " + content
        
        # 时长模式
        patterns = [
            r'(\d+)\s*(?:分钟|min|mins)',
            r'时长[：:]\s*(\d+)',
            r'片长[：:]\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                runtime = int(match.group(1))
                if 1 <= runtime <= 500:
                    return runtime
        
        return 0
    
    def _extract_year_from_text(self, title: str, content: str) -> int:
        """从文本中提取年份"""
        text = title + " " + content
        
        year_match = re.search(r'(19|20)\d{2}', text)
        if year_match:
            year = int(year_match.group())
            if 2000 <= year <= 2030:
                return year
        
        return 0
    
    def _extract_genres_from_text(self, title: str, content: str) -> List[str]:
        """从文本中提取类型/标签"""
        genres = []
        text = title + " " + content
        
        # 常见标签
        tag_keywords = [
            "国产", "台湾", "香港", "中文", "普通话",
            "高清", "HD", "1080P", "4K",
            "中文字幕", "字幕", "内嵌", "外挂",
            "剧情", "偷拍", "自拍", "原创", "精选",
            "巨乳", "美尻", "翘臀", "长腿", "丝袜",
            "制服", "学生", "教师", "护士", "OL",
            "人妻", "熟女", "萝莉", "清纯",
            "SM", "肛交", "颜射", "口交",
            "群交", "乱伦", "换妻",
        ]
        
        for tag in tag_keywords:
            if tag.lower() in text.lower():
                genres.append(tag)
        
        # 提取 [标签] 格式
        tag_matches = re.findall(r'\[([^\]]+)\]', text)
        for tag in tag_matches:
            tag = tag.strip()
            if len(tag) >= 2 and len(tag) <= 6 and tag not in genres:
                # 排除番号格式
                if not re.match(r'^[A-Z]+-?\d+$', tag, re.IGNORECASE):
                    genres.append(tag)
        
        return genres[:10]  # 限制数量
    
    def _extract_plot_from_text(self, content: str) -> str:
        """从文本中提取简介"""
        if not content:
            return ""
        
        # 清理内容
        plot = content.strip()
        
        # 移除图片地址
        plot = re.sub(r'https?://[^\s]+', '', plot)
        
        # 移除多余空白
        plot = ' '.join(plot.split())
        
        # 限制长度
        if len(plot) > 1000:
            plot = plot[:1000] + "..."
        
        return plot
    
    def _extract_images_from_text(self, content: str) -> List[str]:
        """从文本中提取图片链接"""
        images = []
        
        # 提取 img 标签中的 src
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        matches = re.findall(img_pattern, content)
        
        for match in matches:
            if match and not match.endswith('.gif'):
                images.append(match)
        
        return images


# ===== 导出 =====
__all__ = ['XhtScraper']
