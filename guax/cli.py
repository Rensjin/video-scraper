"""
Guax CLI 工具

提供命令行界面用于管理媒体库
"""
import sys
import asyncio
import argparse
from pathlib import Path
from loguru import logger

from guax.core.logger import setup_logger
from guax.core.database import init_db, SessionLocal
from guax.core.models import Media, ScraperSource
from guax.scrapers.manager import get_scraper_manager
from guax.metadata.generator import MetadataGenerator


def setup_args():
    """设置命令行参数"""
    parser = argparse.ArgumentParser(
        description="Guax - 国产成人视频刮削工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  guax init                    # 初始化数据库
  guax scrape MD-001           # 刮削单个媒体
  guax parse "MD-001.mp4"     # 解析文件名
  guax list                    # 列出媒体库
  guax sources                 # 列出刮削源
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # init 命令
    subparsers.add_parser("init", help="初始化数据库")
    
    # scrape 命令
    scrape_parser = subparsers.add_parser("scrape", help="刮削媒体")
    scrape_parser.add_argument("query", help="搜索关键词（番号或标题）")
    scrape_parser.add_argument("-s", "--source", help="指定刮削源", choices=["javdb", "xht"])
    scrape_parser.add_argument("-o", "--output", help="输出目录")
    
    # parse 命令
    parse_parser = subparsers.add_parser("parse", help="解析文件名")
    parse_parser.add_argument("filename", help="文件名或路径")
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="列出媒体库")
    list_parser.add_argument("-l", "--limit", type=int, default=50, help="限制数量")
    
    # sources 命令
    subparsers.add_parser("sources", help="列出刮削源")
    
    # generate 命令
    gen_parser = subparsers.add_parser("generate", help="生成 NFO")
    gen_parser.add_argument("media_id", type=int, help="媒体 ID")
    gen_parser.add_argument("-o", "--output", help="输出目录")
    
    return parser


async def cmd_scrape(args):
    """刮削命令"""
    manager = get_scraper_manager()
    
    logger.info(f"正在刮削: {args.query}")
    
    sources = [args.source] if args.source else None
    result = await manager.scrape(args.query, sources=sources)
    
    if result:
        print("\n=== 刮削结果 ===")
        print(f"标题: {result.title}")
        print(f"番号: {result.source_code}")
        print(f"片商: {result.studio_zh or result.studio}")
        print(f"发行日期: {result.release_date}")
        print(f"时长: {result.runtime_str or result.runtime}")
        print(f"评分: {result.rating}")
        print(f"类型: {', '.join(result.genres[:5])}")
        print(f"演员: {', '.join(result.actors[:5])}")
        if result.plot:
            print(f"\n简介:\n{result.plot[:200]}...")
        if args.output:
            generator = MetadataGenerator()
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            nfo_path = generator.nfo_generator.generate_nfo(result, str(output_dir / f"{result.source_code or result.title}.nfo"))
            logger.info(f"NFO 已保存: {nfo_path}")
    else:
        logger.error("未找到匹配结果")
        return 1
    
    return 0


async def cmd_parse(args):
    """解析文件名命令"""
    manager = get_scraper_manager()
    
    result = manager.parse_filename(args.filename)
    
    print("\n=== 解析结果 ===")
    print(f"原始文件名: {result.original}")
    print(f"番号: {result.code or '未识别'}")
    print(f"平台: {result.platform or '未识别'}")
    print(f"中文标题: {result.title_cn or '未识别'}")
    print(f"年份: {result.year or '未识别'}")
    print(f"集数: {result.part or '无'}")
    print(f"演员: {', '.join(result.actors) if result.actors else '未识别'}")
    print(f"置信度: {result.confidence * 100:.1f}%")
    print(f"解析状态: {'成功' if result.is_valid else '失败'}")
    
    return 0


async def cmd_list(args):
    """列出媒体库命令"""
    db = SessionLocal()
    try:
        items = db.query(Media).order_by(Media.updated_at.desc()).limit(args.limit).all()
        
        if not items:
            print("媒体库为空")
            return 0
        
        print(f"\n=== 媒体库 (共 {len(items)} 条) ===")
        print(f"{'ID':<4} {'标题':<40} {'番号':<15} {'片商':<15} {'刮削源':<10}")
        print("-" * 85)
        
        for item in items:
            title = (item.title or '')[:38]
            code = (item.source_id or '')[:13]
            studio = (item.studio_zh or item.studio or '')[:13]
            source = (item.source or '')[:8]
            print(f"{item.id:<4} {title:<40} {code:<15} {studio:<15} {source:<10}")
        
        return 0
    finally:
        db.close()


async def cmd_sources(args):
    """列出刮削源命令"""
    manager = get_scraper_manager()
    sources = manager.list_scrapers()
    
    print("\n=== 可用刮削源 ===")
    print(f"{'名称':<15} {'显示名称':<20} {'优先级':<10} {'状态':<10}")
    print("-" * 55)
    
    for source in sources:
        name = source['name'][:13]
        display = source['display_name'][:18]
        priority = str(source['priority'])
        status = '已启用' if source['enabled'] else '已禁用'
        print(f"{name:<15} {display:<20} {priority:<10} {status:<10}")
    
    return 0


async def cmd_generate(args):
    """生成 NFO 命令"""
    db = SessionLocal()
    try:
        media = db.query(Media).filter(Media.id == args.media_id).first()
        
        if not media:
            logger.error(f"媒体不存在: {args.media_id}")
            return 1
        
        from guax.scrapers.base import MediaMetadata
        
        metadata = MediaMetadata(
            title=media.title,
            original_title=media.original_title,
            studio=media.studio,
            studio_zh=media.studio_zh,
            series=media.series,
            director=media.director,
            actors=media.actors.split(',') if media.actors else [],
            genres=media.genres.split(',') if media.genres else [],
            release_date=media.release_date,
            year=media.year,
            runtime=media.runtime,
            rating=media.rating,
            plot=media.plot,
            source_code=media.source_id,
            source_name=media.source,
        )
        
        generator = MetadataGenerator()
        output_dir = args.output or str(Path.cwd() / "output")
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        nfo_path = generator.nfo_generator.generate_nfo(metadata, str(output_dir / f"{media.source_id or media.title}.nfo"))
        logger.info(f"NFO 已生成: {nfo_path}")
        
        return 0
    finally:
        db.close()


def main():
    """主入口"""
    # 设置日志
    setup_logger()
    
    # 解析参数
    parser = setup_args()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # 执行命令
    try:
        if args.command == "init":
            logger.info("初始化数据库...")
            init_db()
            logger.info("数据库初始化完成")
            
            # 添加默认刮削源
            db = SessionLocal()
            try:
                default_sources = [
                    ScraperSource(name="javdb", display_name="JavDB", priority=10, enabled=True),
                    ScraperSource(name="xht", display_name="色花堂/1024", priority=20, enabled=True),
                ]
                for source in default_sources:
                    existing = db.query(ScraperSource).filter(ScraperSource.name == source.name).first()
                    if not existing:
                        db.add(source)
                db.commit()
                logger.info("默认刮削源已添加")
            finally:
                db.close()
            
            return 0
        
        elif args.command == "scrape":
            return asyncio.run(cmd_scrape(args))
        
        elif args.command == "parse":
            return asyncio.run(cmd_parse(args))
        
        elif args.command == "list":
            return asyncio.run(cmd_list(args))
        
        elif args.command == "sources":
            return asyncio.run(cmd_sources(args))
        
        elif args.command == "generate":
            return asyncio.run(cmd_generate(args))
        
        else:
            parser.print_help()
            return 1
    
    except KeyboardInterrupt:
        logger.info("已取消")
        return 130
    except Exception as e:
        logger.exception(f"执行失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
