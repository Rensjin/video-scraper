"""媒体库 API"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc

from guax.core.database import get_db
from guax.core.models import Media, ScrapeTask

router = APIRouter(prefix="/api/library", tags=["library"])


@router.get("/")
async def list_media(
    skip: int = 0,
    limit: int = 50,
    scraped_only: bool = False,
    db: Session = Depends(get_db)
):
    """列出媒体库中的所有媒体"""
    query = db.query(Media)
    
    if scraped_only:
        query = query.filter(Media.is_scrapped == True)
    
    total = query.count()
    items = query.order_by(desc(Media.updated_at)).offset(skip).limit(limit).all()
    
    return {
        "success": True,
        "data": [item.to_dict() for item in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{media_id}")
async def get_media(media_id: int, db: Session = Depends(get_db)):
    """获取单个媒体详情"""
    media = db.query(Media).filter(Media.id == media_id).first()
    
    if not media:
        raise HTTPException(status_code=404, detail="媒体不存在")
    
    return {
        "success": True,
        "data": _media_to_dict(media)
    }


@router.post("/")
async def create_media(
    file_path: str = Form(...),
    file_name: str = Form(...),
    title: str = Form(...),
    original_title: str = Form(""),
    studio: str = Form(""),
    studio_zh: str = Form(""),
    series: str = Form(""),
    director: str = Form(""),
    actors: str = Form(""),
    genres: str = Form(""),
    release_date: str = Form(""),
    year: int = Form(0),
    runtime: int = Form(0),
    rating: float = Form(0.0),
    plot: str = Form(""),
    poster_path: str = Form(""),
    backdrop_path: str = Form(""),
    source: str = Form(""),
    source_id: str = Form(""),
    source_url: str = Form(""),
    db: Session = Depends(get_db)
):
    """创建媒体条目"""
    media = Media(
        file_path=file_path,
        file_name=file_name,
        title=title,
        original_title=original_title,
        studio=studio,
        studio_zh=studio_zh,
        series=series,
        director=director,
        actors=actors,
        genres=genres,
        release_date=release_date,
        year=year,
        runtime=runtime,
        rating=rating,
        plot=plot,
        poster_path=poster_path,
        backdrop_path=backdrop_path,
        source=source,
        source_id=source_id,
        source_url=source_url,
    )
    
    db.add(media)
    db.commit()
    db.refresh(media)
    
    return {
        "success": True,
        "data": _media_to_dict(media)
    }


@router.put("/{media_id}")
async def update_media(
    media_id: int,
    title: Optional[str] = Form(None),
    original_title: Optional[str] = Form(None),
    studio: Optional[str] = Form(None),
    studio_zh: Optional[str] = Form(None),
    series: Optional[str] = Form(None),
    director: Optional[str] = Form(None),
    actors: Optional[str] = Form(None),
    genres: Optional[str] = Form(None),
    release_date: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    runtime: Optional[int] = Form(None),
    rating: Optional[float] = Form(None),
    plot: Optional[str] = Form(None),
    poster_path: Optional[str] = Form(None),
    backdrop_path: Optional[str] = Form(None),
    is_scrapped: Optional[bool] = Form(None),
    db: Session = Depends(get_db)
):
    """更新媒体信息"""
    media = db.query(Media).filter(Media.id == media_id).first()
    
    if not media:
        raise HTTPException(status_code=404, detail="媒体不存在")
    
    # 更新字段
    update_fields = {
        "title": title,
        "original_title": original_title,
        "studio": studio,
        "studio_zh": studio_zh,
        "series": series,
        "director": director,
        "actors": actors,
        "genres": genres,
        "release_date": release_date,
        "year": year,
        "runtime": runtime,
        "rating": rating,
        "plot": plot,
        "poster_path": poster_path,
        "backdrop_path": backdrop_path,
        "is_scrapped": is_scrapped,
    }
    
    for field, value in update_fields.items():
        if value is not None:
            setattr(media, field, value)
    
    db.commit()
    db.refresh(media)
    
    return {
        "success": True,
        "data": _media_to_dict(media)
    }


@router.delete("/{media_id}")
async def delete_media(media_id: int, db: Session = Depends(get_db)):
    """删除媒体"""
    media = db.query(Media).filter(Media.id == media_id).first()
    
    if not media:
        raise HTTPException(status_code=404, detail="媒体不存在")
    
    db.delete(media)
    db.commit()
    
    return {"success": True}


@router.post("/{media_id}/poster")
async def upload_poster(
    media_id: int,
    poster: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传海报"""
    from pathlib import Path
    import shutil
    
    media = db.query(Media).filter(Media.id == media_id).first()
    
    if not media:
        raise HTTPException(status_code=404, detail="媒体不存在")
    
    # 保存海报
    upload_dir = Path("data/posters")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    poster_path = upload_dir / f"{media_id}_{poster.filename}"
    
    with open(poster_path, "wb") as f:
        shutil.copyfileobj(poster.file, f)
    
    # 更新数据库
    media.poster_path = str(poster_path)
    db.commit()
    
    return {
        "success": True,
        "data": {"poster_path": str(poster_path)}
    }


def _media_to_dict(media: Media) -> dict:
    """将 Media 模型转换为字典"""
    return {
        "id": media.id,
        "file_path": media.file_path,
        "file_name": media.file_name,
        "file_size": media.file_size,
        "title": media.title,
        "original_title": media.original_title,
        "studio": media.studio,
        "studio_zh": media.studio_zh,
        "series": media.series,
        "director": media.director,
        "actors": media.actors,
        "genres": media.genres,
        "release_date": media.release_date,
        "year": media.year,
        "runtime": media.runtime,
        "rating": media.rating,
        "plot": media.plot,
        "poster_path": media.poster_path,
        "backdrop_path": media.backdrop_path,
        "source": media.source,
        "source_id": media.source_id,
        "source_url": media.source_url,
        "is_scrapped": media.is_scrapped,
        "is_nfo_generated": media.is_nfo_generated,
        "created_at": media.created_at.isoformat() if media.created_at else None,
        "updated_at": media.updated_at.isoformat() if media.updated_at else None,
    }
