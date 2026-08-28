"""日志配置"""
import sys
from pathlib import Path
from loguru import logger

def setup_logger(log_file: str = "logs/guax.log", level: str = "INFO"):
    """配置日志系统"""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=level
    )
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_file,
        rotation="10 MB",
        retention="30 days",
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
    )
    return logger
