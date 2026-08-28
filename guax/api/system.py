"""系统 API"""
from fastapi import APIRouter, HTTPException
from guax.core.config import settings, load_config
from guax.core.database import init_db

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "version": "0.1.0",
        "name": "Guax",
    }


@router.get("/config")
async def get_config():
    """获取配置"""
    return {
        "success": True,
        "data": {
            "app": {
                "name": settings.app.name,
                "port": settings.app.port,
            },
            "scraper": {
                "enabled_sources": settings.scraper.enabled_sources,
            }
        }
    }


@router.post("/init-db")
async def initialize_database():
    """初始化数据库"""
    try:
        init_db()
        return {"success": True, "message": "数据库初始化成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload-config")
async def reload_config(config_path: str = "config/config.yaml"):
    """重新加载配置"""
    global settings
    settings = load_config(config_path)
    return {"success": True, "message": "配置已重新加载"}
