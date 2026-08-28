"""
Guax Web 应用

基于 FastAPI + Vue 3 的 Web 界面
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os

from guax.core.config import settings
from guax.core.logger import setup_logger
from guax.core.database import init_db

# 初始化日志
logger = setup_logger()

# 创建 FastAPI 应用
app = FastAPI(
    title="Guax - 本地视频元数据刮削工具",
    description="基于 Amane 二创的本地视频元数据刮削工具",
    version="0.1.0",
)

# 静态文件
static_dir = Path(__file__).parent.parent.parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 模板
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# 导入路由
from guax.api import scrape, library, system


@app.on_event("startup")
async def startup():
    """应用启动"""
    logger.info("Guax 启动中...")
    
    # 初始化数据库
    try:
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.warning(f"数据库初始化警告: {e}")
    
    logger.info(f"Guax 启动完成，访问 http://localhost:{settings.app.port}")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": settings.app.name,
        "version": "0.1.0",
    })


@app.get("/api")
async def api_info():
    """API 信息"""
    return {
        "name": "Guax API",
        "version": "0.1.0",
        "docs": "/docs",
    }


# 注册路由
app.include_router(scrape.router)
app.include_router(library.router)
app.include_router(system.router)
