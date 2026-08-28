"""刮削 API"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from guax.core.database import get_db
from guax.core.models import Media, ScrapeTask, ScraperSource
from guax.scrapers.manager import get_scraper_manager, ScraperManager
from guax.metadata.generator import MetadataGenerator

router = APIRouter(prefix="/api", tags=["scrape"])


class ScrapeRequest(BaseModel):
    """刮削请求"""
    query: str
    sources: Optional[List[str]] = None
    prefer_source: Optional[str] = None


class ScrapeResponse(BaseModel):
    """刮削响应"""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


@router.get("/sources")
async def list_sources():
    """列出所有刮削源"""
    manager = get_scraper_manager()
    return {
        "success": True,
        "data": manager.list_scrapers()
    }


@router.post("/scrape")
async def scrape_media(
    query: str = Form(...),
    source: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """刮削单个媒体"""
    try:
        manager = get_scraper_manager()
        
        # 执行刮削
        if source:
            result = await manager.scrape(query, sources=[source])
        else:
            result = await manager.scrape(query)
        
        if result:
            return {
                "success": True,
                "data": result.to_dict()
            }
        else:
            return {
                "success": False,
                "error": "未找到匹配结果"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/scrape/file")
async def scrape_file(
    file: UploadFile = File(...),
    sources: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """从上传的文件刮削"""
    try:
        # 读取文件名
        filename = file.filename or "unknown"
        
        manager = get_scraper_manager()
        
        # 解析文件名
        parsed = manager.parse_filename(filename)
        
        # 刮削
        source_list = sources.split(",") if sources else None
        result = await manager.scrape_from_file(filename, sources=source_list)
        
        if result:
            return {
                "success": True,
                "data": {
                    "parsed": {
                        "code": parsed.code,
                        "title": parsed.title_cn,
                        "platform": parsed.platform,
                        "confidence": parsed.confidence,
                    },
                    "metadata": result.to_dict()
                }
            }
        else:
            return {
                "success": False,
                "error": "未找到匹配结果",
                "parsed": {
                    "code": parsed.code,
                    "title": parsed.title_cn,
                    "platform": parsed.platform,
                    "confidence": parsed.confidence,
                }
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/scrape/batch")
async def batch_scrape(
    queries: List[str] = Form(...),
    sources: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """批量刮削"""
    try:
        manager = get_scraper_manager()
        source_list = sources.split(",") if sources else None
        
        results = await manager.batch_scrape(queries, sources=source_list)
        
        return {
            "success": True,
            "data": [r.to_dict() if r else None for r in results]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/generate/nfo")
async def generate_nfo(
    query: str = Form(...),
    output_dir: str = Form(...),
    db: Session = Depends(get_db)
):
    """生成 NFO 文件"""
    try:
        manager = get_scraper_manager()
        metadata = await manager.scrape(query)
        
        if not metadata:
            return {"success": False, "error": "未找到匹配结果"}
        
        generator = MetadataGenerator()
        result = generator.generate_all(
            metadata=metadata,
            output_dir=output_dir,
            video_filename=f"{metadata.source_code or metadata.title}.mp4"
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/parse/filename")
async def parse_filename(
    filename: str = Form(...),
):
    """解析文件名"""
    try:
        manager = get_scraper_manager()
        parsed = manager.parse_filename(filename)
        
        return {
            "success": True,
            "data": {
                "original": parsed.original,
                "code": parsed.code,
                "code_prefix": parsed.code_prefix,
                "code_number": parsed.code_number,
                "title": parsed.title_cn,
                "platform": parsed.platform,
                "series": parsed.series,
                "part": parsed.part,
                "episode": parsed.episode,
                "disc": parsed.disc,
                "actors": parsed.actors,
                "genres": parsed.genres,
                "year": parsed.year,
                "confidence": parsed.confidence,
                "is_valid": parsed.is_valid,
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
