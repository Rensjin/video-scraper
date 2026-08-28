"""
本地视频文件名解析器

支持解析的片商/平台模式：
- MD / MDB 系列
- SWAG 系列
- 91 系列
- XS 系列
- SQ 系列
- SG 系列
- NnUU 系列
- HEYZO 系列
- Tokyo-Hot 系列
- 以及各种自定义命名规则
"""
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from loguru import logger


@dataclass
class ParsedFilename:
    """解析后的文件名结构"""
    # 原始输入
    original: str = ""
    file_path: str = ""
    file_name: str = ""
    file_ext: str = ""
    
    # 解析结果
    code: str = ""  # 番号/编号，如 MD-001, SWAG-001
    code_prefix: str = ""  # 前缀，如 MD, SWAG, 91
    code_number: str = ""  # 编号，如 001
    
    # 元数据
    title: str = ""
    title_cn: str = ""
    series: str = ""
    part: str = ""  # 第N集/第N部
    episode: int = 0
    disc: str = ""  # 盘号 CD1, CD2
    
    # 演员
    actors: List[str] = field(default_factory=list)
    
    # 类型/标签
    genres: List[str] = field(default_factory=list)
    
    # 年份
    year: int = 0
    
    # 解析到的平台
    platform: str = ""
    
    # 置信度
    confidence: float = 0.0
    
    # 额外信息
    extra: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_valid(self) -> bool:
        """是否解析成功"""
        return bool(self.code or self.title)
    
    def __repr__(self):
        return f"<ParsedFilename(code='{self.code}', title='{self.title}', platform='{self.platform}')>"


class ChineseAdultPattern:
    """国产成人视频文件名模式定义"""
    
    # ===== 片商/平台模式 =====
    
    # 麻豆传媒 - MD 系列
    MD_PATTERN = re.compile(
        r'(?:MD[-_]?0*(\d+)|'
        r'MADOU[-_]?|麻豆[-_]?)'
        r'(\d+)',
        re.IGNORECASE
    )
    
    # MDB 系列
    MDB_PATTERN = re.compile(r'MDB[-_]?(\d+)', re.IGNORECASE)
    
    # SWAG 系列
    SWAG_PATTERN = re.compile(
        r'(?:SWAG[-_]?|swag[-_]?)(\d+)',
        re.IGNORECASE
    )
    
    # 91 系列（91破解/91分享等）
    V91_PATTERN = re.compile(
        r'(?:91[-_]?|91[国产日本韩国欧美]?[-_]?)(\w+)',
        re.IGNORECASE
    )
    
    # XS 系列（新蝴蝶/小三元等）
    XS_PATTERN = re.compile(
        r'(?:XS[-_]?|xs[-_]?)(\d+)',
        re.IGNORECASE
    )
    
    # SQ 系列（系列番号）
    SQ_PATTERN = re.compile(
        r'(?:SQ[-_]?|series[-_]?)(\d+)',
        re.IGNORECASE
    )
    
    # SG 系列
    SG_PATTERN = re.compile(
        r'(?:SG[-_]?(\d+))',
        re.IGNORECASE
    )
    
    # NnUU / 奶牛 系列
    NnUU_PATTERN = re.compile(
        r'(?:NnUU[-_]?|nnuu[-_]?|nn[-_]?|奶牛[-_]?)(\d+)',
        re.IGNORECASE
    )
    
    # HEYZO 系列（虽然不是国产但常一起处理）
    HEYZO_PATTERN = re.compile(
        r'(?:HEYZO[-_]?|heyzo[-_]?)(\d+)',
        re.IGNORECASE
    )
    
    # Tokyo-Hot 系列
    TH_PATTERN = re.compile(
        r'(?:Tokyo-Hot[-_]?|TH[-_]?|tkoht[-_]?)(\w+)',
        re.IGNORECASE
    )
    
    # 10musume 系列
    TM_PATTERN = re.compile(
        r'(?:10musume[-_]?|10mu[-_]?)(\d+)',
        re.IGNORECASE
    )
    
    # 1Pondo 系列
    OP_PATTERN = re.compile(
        r'(?:1Pondo[-_]?|1P[-_]?)(\d+)',
        re.IGNORECASE
    )
    
    # Carib 系列（加勒比）
    CARIB_PATTERN = re.compile(
        r'(?:Caribbean[-_]?|carib[-_]?|GQR-?)(\d+)',
        re.IGNORECASE
    )
    
    # 各种无码系列
    N0101_PATTERN = re.compile(r'N0101[-_]?(\d+)', re.IGNORECASE)
    
    # 国产自制常见命名
    # 如: 国产偷拍、国产剧情、精品国产等
    CN_PLATFORM_PATTERN = re.compile(
        r'(?:国产|中文|国语|普通话)'
        r'(?:精品|独家|偷拍|剧情|自拍|原创)?'
        r'(?:视频|短片|作品|系列)?',
        re.IGNORECASE
    )
    
    # ===== 通用模式 =====
    
    # 年份
    YEAR_PATTERN = re.compile(r'(?:19|20)\d{2}')
    
    # 集数/分部
    PART_PATTERN = re.compile(
        r'(?:第?\s*(\d+)\s*(?:集|部|话|弹|发|段|期)|'
        r'(?:CD|DISC|disc)\s*(\d+)|'
        r'(?:Part|part|PART)\s*(\d+))',
        re.IGNORECASE
    )
    
    # 清晰度
    RESOLUTION_PATTERN = re.compile(
        r'(?:4K|8K|1080[PI]|720[PI]|2160[PI]|480[PI]|[HS]D|'
        r'WEB[-]?DL|BLURAY|BRRip|HDRip|DVDRip|X264|X265)',
        re.IGNORECASE
    )
    
    # 字幕标识
    SUBTITLE_PATTERN = re.compile(
        r'(?:字幕|中字|字幕版|CN|chs|cht|简|繁|日字|内嵌|外挂)',
        re.IGNORECASE
    )
    
    # 平台关键词映射
    PLATFORM_KEYWORDS: Dict[str, List[str]] = {
        "MD": ["md", "madou", "麻豆", "传媒"],
        "MDB": ["mdb", "mdbang"],
        "SWAG": ["swag"],
        "91": ["91", "91破解", "91分享", "91坛"],
        "XS": ["xs", "新蝴蝶", "小三元"],
        "SG": ["sg", "series"],
        "NnUU": ["nnuu", "nn", "nnuts", "奶牛"],
        "HEYZO": ["heyzo"],
        "Tokyo-Hot": ["tokyo-hot", "th", "tkoht"],
        "10musume": ["10musume", "10mu"],
        "1Pondo": ["1pondo", "1p"],
        "Carib": ["carib", "caribbean", "gqr", "加勒比"],
        "N0101": ["n0101"],
    }
    
    # 片商/工作室名称映射（用于解析中文标题中的片商）
    STUDIO_ALIAS: Dict[str, str] = {
        "md": "麻豆传媒",
        "madou": "麻豆传媒",
        "swag": "SWAG",
        "91": "91原创",
        "xs": "XS系列",
        "nnuu": "NnUU",
        "heyzo": "HEYZO",
        "tokyo-hot": "Tokyo-Hot",
        "carib": "Carib",
        "gqr": "Carib",
    }


class FilenameParser:
    """国产成人视频文件名解析器"""
    
    def __init__(self, custom_patterns: Optional[List[Dict[str, Any]]] = None):
        self.patterns = ChineseAdultPattern()
        self.custom_patterns = custom_patterns or []
    
    def parse(self, filename: str, file_path: Optional[str] = None) -> ParsedFilename:
        """
        解析文件名
        
        Args:
            filename: 文件名或完整路径
            file_path: 完整路径（可选）
            
        Returns:
            ParsedFilename 解析结果
        """
        result = ParsedFilename()
        
        # 原始输入
        result.original = filename
        result.file_path = file_path or filename
        
        # 提取文件名（去掉路径）
        if file_path:
            p = Path(file_path)
            result.file_name = p.stem
            result.file_ext = p.suffix.lower()
        else:
            p = Path(filename)
            result.file_name = p.stem
            result.file_ext = p.suffix.lower()
        
        # 清理文件名
        cleaned = self._clean_filename(result.file_name)
        
        # 解析番号
        code_info = self._extract_code(cleaned)
        if code_info:
            result.code = code_info['code']
            result.code_prefix = code_info['prefix']
            result.code_number = code_info['number']
            result.platform = code_info['platform']
            result.confidence = code_info['confidence']
        
        # 解析集数/分部
        part_info = self._extract_part(cleaned)
        if part_info:
            result.part = part_info['part']
            result.episode = part_info['episode']
            result.disc = part_info['disc']
        
        # 解析年份
        year = self._extract_year(cleaned)
        if year:
            result.year = year
        
        # 解析分辨率
        resolution = self._extract_resolution(cleaned)
        if resolution:
            result.extra['resolution'] = resolution
        
        # 解析字幕信息
        has_subtitle = self._has_subtitle(cleaned)
        if has_subtitle:
            result.extra['has_subtitle'] = True
            result.genres.append("中文字幕")
        
        # 尝试从文件名提取标题
        title = self._extract_title(cleaned, result)
        if title:
            result.title_cn = title
        
        # 解析演员
        actors = self._extract_actors(cleaned)
        if actors:
            result.actors = actors
        
        # 如果有番号，生成标题
        if result.code and not result.title_cn:
            result.title_cn = f"{self.patterns.STUDIO_ALIAS.get(result.platform, result.platform)}-{result.code}"
        
        # 计算置信度
        result.confidence = self._calculate_confidence(result)
        
        return result
    
    def _clean_filename(self, filename: str) -> str:
        """清理文件名"""
        # 移除常见无用字符
        cleaned = filename
        
        # 移除扩展名相关
        cleaned = re.sub(r'\.(mp4|mkv|avi|mov|wmv|flv|webm|m4v)$', '', cleaned, flags=re.IGNORECASE)
        
        # 移除常见标记
        markers = [
            r'\[.*?\]',  # [xxx]
            r'（.*?）',  # （xxx）
            r'\(.*?\)',  # (xxx)
            r'【.*?】',  # 【xxx】
        ]
        for marker in markers:
            cleaned = re.sub(marker, ' ', cleaned)
        
        # 移除下划线连字符为空格
        cleaned = re.sub(r'[-_]+', ' ', cleaned)
        
        # 移除多余空格
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    def _extract_code(self, filename: str) -> Optional[Dict[str, Any]]:
        """提取番号"""
        # 按优先级尝试匹配
        patterns = [
            # MD 系列（麻豆传媒）
            (self.patterns.MD_PATTERN, "MD", "MD"),
            
            # MDB 系列
            (self.patterns.MDB_PATTERN, "MDB", "MDB"),
            
            # SWAG 系列
            (self.patterns.SWAG_PATTERN, "SWAG", "SWAG"),
            
            # NnUU 系列
            (self.patterns.NnUU_PATTERN, "NnUU", "NnUU"),
            
            # HEYZO 系列
            (self.patterns.HEYZO_PATTERN, "HEYZO", "HEYZO"),
            
            # Tokyo-Hot 系列
            (self.patterns.TH_PATTERN, "TH", "Tokyo-Hot"),
            
            # 10musume 系列
            (self.patterns.TM_PATTERN, "10musume", "10musume"),
            
            # 1Pondo 系列
            (self.patterns.OP_PATTERN, "1P", "1Pondo"),
            
            # Carib 系列
            (self.patterns.CARIB_PATTERN, "CARIB", "Carib"),
            
            # N0101 系列
            (self.patterns.N0101_PATTERN, "N0101", "N0101"),
            
            # 91 系列
            (self.patterns.V91_PATTERN, "91", "91"),
            
            # XS 系列
            (self.patterns.XS_PATTERN, "XS", "XS"),
            
            # SQ 系列
            (self.patterns.SQ_PATTERN, "SQ", "SQ"),
            
            # SG 系列
            (self.patterns.SG_PATTERN, "SG", "SG"),
        ]
        
        for pattern, prefix, platform in patterns:
            match = pattern.search(filename)
            if match:
                number = match.group(1) if match.lastindex else ""
                code = f"{prefix}-{number}" if number else prefix
                confidence = 0.9 if number else 0.7
                
                return {
                    'code': code,
                    'prefix': prefix,
                    'number': number,
                    'platform': platform,
                    'confidence': confidence
                }
        
        return None
    
    def _extract_part(self, filename: str) -> Optional[Dict[str, Any]]:
        """提取集数/分部"""
        match = self.patterns.PART_PATTERN.search(filename)
        if match:
            for i in range(1, match.lastindex + 1):
                if match.group(i):
                    episode = int(match.group(i))
                    return {
                        'episode': episode,
                        'part': f"第{episode}部",
                        'disc': f"CD{episode}" if 'cd' in match.group().lower() else match.group()
                    }
        return None
    
    def _extract_year(self, filename: str) -> int:
        """提取年份"""
        match = self.patterns.YEAR_PATTERN.search(filename)
        if match:
            year = int(match.group())
            if 1990 <= year <= 2030:
                return year
        return 0
    
    def _extract_resolution(self, filename: str) -> str:
        """提取分辨率"""
        match = self.patterns.RESOLUTION_PATTERN.search(filename)
        if match:
            return match.group().upper()
        return ""
    
    def _has_subtitle(self, filename: str) -> bool:
        """检查是否有字幕标识"""
        return bool(self.patterns.SUBTITLE_PATTERN.search(filename))
    
    def _extract_title(self, filename: str, result: ParsedFilename) -> str:
        """提取标题"""
        title = filename
        
        # 移除番号部分
        if result.code:
            title = re.sub(re.escape(result.code), '', title, flags=re.IGNORECASE)
        
        # 移除年份
        title = self.patterns.YEAR_PATTERN.sub('', title)
        
        # 移除分辨率
        res_match = self.patterns.RESOLUTION_PATTERN.search(title)
        if res_match:
            title = title.replace(res_match.group(), '')
        
        # 移除多余字符
        title = re.sub(r'[-_\s]+', ' ', title)
        title = title.strip()
        
        # 限制长度
        if len(title) > 100:
            title = title[:100]
        
        return title if title else ""
    
    def _extract_actors(self, filename: str) -> List[str]:
        """提取演员（从文件名中）"""
        actors = []
        
        # 常见模式：@xxx 或 at xxx
        at_match = re.search(r'[@@]?\s*(\w+)', filename)
        if at_match:
            actor = at_match.group(1).strip()
            if len(actor) >= 2:
                actors.append(actor)
        
        return actors
    
    def _calculate_confidence(self, result: ParsedFilename) -> float:
        """计算解析置信度"""
        confidence = result.confidence if result.confidence > 0 else 0.5
        
        # 有番号加一分
        if result.code:
            confidence += 0.1
        
        # 有标题加一分
        if result.title_cn:
            confidence += 0.1
        
        # 有年份加一分
        if result.year:
            confidence += 0.05
        
        # 有集数加一分
        if result.episode:
            confidence += 0.05
        
        # 有演员加一分
        if result.actors:
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def batch_parse(self, filenames: List[str]) -> List[ParsedFilename]:
        """批量解析"""
        return [self.parse(fn) for fn in filenames]
    
    def add_custom_pattern(self, name: str, pattern: str, prefix: str, platform: str):
        """添加自定义模式"""
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
            self.custom_patterns.append({
                'name': name,
                'pattern': compiled,
                'prefix': prefix,
                'platform': platform
            })
        except re.error as e:
            logger.error(f"无效的正则表达式: {pattern}, error: {e}")
    
    def get_platform_info(self, platform: str) -> Optional[Dict[str, Any]]:
        """获取平台信息"""
        keywords = self.patterns.PLATFORM_KEYWORDS.get(platform.upper())
        if not keywords:
            return None
        
        return {
            'name': platform,
            'keywords': keywords,
            'alias': self.patterns.STUDIO_ALIAS.get(platform.lower(), platform),
        }


# ===== 导出 =====
__all__ = ['FilenameParser', 'ParsedFilename', 'ChineseAdultPattern']
