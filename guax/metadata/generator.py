"""
NFO 元数据生成器

生成 Kodi/Emby/Jellyfin 兼容的 NFO 文件
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from xml.etree import ElementTree as ET
from loguru import logger

from guax.scrapers.base import MediaMetadata


class NfoGenerator:
    """NFO 文件生成器"""
    
    # NFO 文件模板
    NFO_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<movie>
  <title>{title}</title>
  <originaltitle>{original_title}</originaltitle>
  <sorttitle>{sort_title}</sorttitle>
  <year>{year}</year>
  <plot>{plot}</plot>
  <outline>{outline}</outline>
  <runtime>{runtime}</runtime>
  <rating>{rating}</rating>
  <votes>{votes}</votes>
  <criticrating>{critic_rating}</criticrating>
  <mpaa>NC-17</mpaa>
  <premiered>{release_date}</premiered>
  <release>{release_date}</release>
  <studio>{studio}</studio>
  <set>{series}</set>
  <director>{director}</director>
  {genres}
  {actors}
  {tags}
  <countrycode>CN</countrycode>
  <language>Chinese</language>
  <subtitles>Chinese</subtitles>
  <uniqueid type="{source_type}" default="true">{source_id}</uniqueid>
  <fanart>
    <thumb>{fanart_url}</thumb>
  </fanart>
  <thumb aspect="poster">{poster_url}</thumb>
</movie>
'''
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def generate_nfo(self, metadata: MediaMetadata, output_path: str) -> str:
        """
        生成 NFO 文件
        
        Args:
            metadata: 媒体元数据
            output_path: 输出路径
            
        Returns:
            NFO 文件路径
        """
        try:
            # 确保目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 构建 NFO 内容
            nfo_content = self._build_nfo_content(metadata)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(nfo_content)
            
            logger.info(f"NFO 文件已生成: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"生成 NFO 文件失败: {e}")
            raise
    
    def _build_nfo_content(self, metadata: MediaMetadata) -> str:
        """构建 NFO 内容"""
        # 格式化排序标题
        sort_title = self._format_sort_title(metadata.title)
        
        # 清理 XML 特殊字符
        plot = self._escape_xml(metadata.plot or "")
        outline = self._escape_xml(metadata.outline or metadata.plot[:200] or "")
        
        # 生成类型标签
        genres_xml = self._generate_genres_xml(metadata.genres)
        actors_xml = self._generate_actors_xml(metadata.actors)
        tags_xml = self._generate_tags_xml(metadata)
        
        # 确定源类型
        source_type = self._get_source_type(metadata.source_name)
        
        return self.NFO_TEMPLATE.format(
            title=self._escape_xml(metadata.title),
            original_title=self._escape_xml(metadata.original_title or metadata.title),
            sort_title=sort_title,
            year=metadata.year or 0,
            plot=plot,
            outline=outline,
            runtime=metadata.runtime or 0,
            rating=metadata.rating or 0.0,
            votes=metadata.rating_count or 0,
            critic_rating=metadata.rating or 0.0,
            release_date=metadata.release_date or "",
            studio=self._escape_xml(metadata.studio_zh or metadata.studio or ""),
            series=self._escape_xml(metadata.series or ""),
            director=self._escape_xml(metadata.director or ""),
            genres=genres_xml,
            actors=actors_xml,
            tags=tags_xml,
            source_type=source_type,
            source_id=self._escape_xml(metadata.source_id or metadata.source_code or ""),
            poster_url=self._escape_xml(metadata.poster_url or ""),
            fanart_url=self._escape_xml(metadata.fanart_url or metadata.backdrop_url or ""),
        )
    
    def _escape_xml(self, text: str) -> str:
        """转义 XML 特殊字符"""
        if not text:
            return ""
        text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        return text
    
    def _format_sort_title(self, title: str) -> str:
        """格式化排序标题"""
        if not title:
            return ""
        # 移除特殊字符
        import re
        title = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', title)
        return title.strip()[:100]
    
    def _generate_genres_xml(self, genres: list) -> str:
        """生成类型 XML"""
        if not genres:
            return "<genre>Other</genre>"
        
        lines = []
        for genre in genres[:10]:  # 限制数量
            genre = self._escape_xml(str(genre))
            lines.append(f"  <genre>{genre}</genre>")
        
        return "\n  ".join(lines)
    
    def _generate_actors_xml(self, actors: list) -> str:
        """生成演员 XML"""
        if not actors:
            return "<actor><name>Unknown</name></actor>"
        
        lines = []
        for actor in actors[:20]:  # 限制数量
            actor = self._escape_xml(str(actor))
            lines.append(f"  <actor><name>{actor}</name></actor>")
        
        return "\n  ".join(lines)
    
    def _generate_tags_xml(self, metadata: MediaMetadata) -> str:
        """生成标签 XML"""
        tags = []
        
        # 添加源标签
        if metadata.source_name:
            tags.append(metadata.source_name)
        
        # 添加字幕标签
        if metadata.subtitles:
            tags.extend(metadata.subtitles)
        
        if not tags:
            return ""
        
        lines = []
        for tag in tags[:10]:
            tag = self._escape_xml(str(tag))
            lines.append(f"  <tag>{tag}</tag>")
        
        return "\n  ".join(lines)
    
    def _get_source_type(self, source_name: str) -> str:
        """获取源类型"""
        type_mapping = {
            "javdb": "javdb",
            "xht": "xht",
            "filename": "local",
            "avmoo": "avmoo",
        }
        return type_mapping.get(source_name.lower(), "custom")


class MetadataGenerator:
    """完整的元数据生成器（生成 NFO + 图片）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.nfo_generator = NfoGenerator(config)
    
    def generate_all(
        self,
        metadata: MediaMetadata,
        output_dir: str,
        video_filename: str,
        download_images: bool = True
    ) -> Dict[str, str]:
        """
        生成所有元数据文件
        
        Args:
            metadata: 媒体元数据
            output_dir: 输出目录
            video_filename: 视频文件名
            download_images: 是否下载图片
            
        Returns:
            生成的文件路径字典
        """
        results = {}
        
        try:
            # 确保输出目录存在
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 生成 NFO 文件
            nfo_filename = Path(video_filename).stem + ".nfo"
            nfo_path = output_path / nfo_filename
            self.nfo_generator.generate_nfo(metadata, str(nfo_path))
            results['nfo'] = str(nfo_path)
            
            # 复制/下载封面图
            if metadata.poster_url:
                poster_filename = Path(video_filename).stem + "-poster.jpg"
                poster_path = output_path / poster_filename
                results['poster'] = str(poster_path)
            
            # 复制/下载背景图
            if metadata.backdrop_url or metadata.fanart_url:
                backdrop_filename = Path(video_filename).stem + "-backdrop.jpg"
                backdrop_path = output_path / backdrop_filename
                results['backdrop'] = str(backdrop_path)
            
            logger.info(f"元数据生成完成: {results}")
            
        except Exception as e:
            logger.error(f"生成元数据失败: {e}")
            raise
        
        return results
    
    def generate_for_library(
        self,
        metadata: MediaMetadata,
        library_path: str,
        file_path: str,
        structure: str = "{title}/"
    ) -> Dict[str, str]:
        """
        为媒体库生成元数据
        
        Args:
            metadata: 媒体元数据
            library_path: 媒体库根目录
            file_path: 视频文件路径
            structure: 目录结构模板
            
        Returns:
            生成的文件路径字典
        """
        # 生成目录名
        folder_name = structure.format(
            title=self._sanitize_filename(metadata.title or metadata.source_code or "Unknown"),
            code=metadata.source_code or "",
            year=metadata.year or "",
            studio=metadata.studio_zh or metadata.studio or "",
        )
        
        # 完整输出目录
        output_dir = Path(library_path) / folder_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取视频文件名
        video_filename = Path(file_path).name
        
        # 生成元数据
        return self.generate_all(
            metadata=metadata,
            output_dir=str(output_dir),
            video_filename=video_filename,
            download_images=False  # 库模式通常不下载图片
        )
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名（移除非法字符）"""
        import re
        # Windows 非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        filename = re.sub(illegal_chars, '_', filename)
        # 限制长度
        filename = filename[:200]
        return filename.strip()


# ===== 导出 =====
__all__ = ['NfoGenerator', 'MetadataGenerator']
