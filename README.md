# Guax - 本地视频元数据刮削工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-00a393.svg)](https://fastapi.tiangolo.com/)

> 本项目基于 [Amane](https://github.com/sqzw-x/amane) 进行本地视频元数据刮削功能扩展。

## 项目简介

Guax 是一款本地视频元数据刮削工具，支持通过番号、文件名、中文标题等多种方式刮削元数据，自动生成 Emby/Jellyfin/Kodi 兼容的 NFO 文件和海报。

### 核心特性

- **多源刮削**：支持 JavDB 等数据源
- **智能解析**：自动识别视频番号
- **离线优先**：本地解析 + 在线刮削混合方案
- **NFO 生成**：自动生成 Kodi/Emby/Jellyfin 兼容的元数据文件
- **Web UI**：完整的可视化界面，支持批量刮削
- **媒体库管理**：本地媒体库管理，支持海报墙

## 技术栈

- **后端**: FastAPI + SQLAlchemy
- **前端**: Vue 3 + Element Plus
- **数据库**: SQLite
- **刮削**: httpx + BeautifulSoup

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/Rensjin/guax.git
cd guax

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 运行

```bash
# 初始化数据库
python -m guax init

# 启动服务
python -m guax
# 或
uvicorn guax.web.app:app --reload --port 8000
```

访问 http://localhost:8000 即可使用。

### Docker 部署

#### 方式一：本地构建

```bash
docker build -t guax .
docker run -d -p 8000:8000 -v ./data:/app/data -v ./config:/app/config guax
```

#### 方式二：使用 Docker Compose

`docker-compose.yml`：

```yaml
services:
  guax:
    image: guax:latest
    container_name: guax
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - TZ=Asia/Shanghai
```

启动服务：

```bash
# 启动
docker compose up -d

# 查看日志
docker compose logs -f

# 停止
docker compose down
```

#### 方式三：NAS 镜像导入（推荐用于无公网环境）

适用于绿联/极空间等 NAS，以及内网/无法拉取 Docker Hub 镜像的环境。

**1. 在有 Docker 的机器上构建并导出镜像**

```bash
# 构建镜像
docker build -t guax:latest .

# 导出为 tar 文件
docker save -o guax-latest.tar guax:latest
```

**2. 把以下文件传到 NAS：**
- `guax-latest.tar`（镜像包）
- `docker-compose.yml`

**3. 在 NAS 上导入并启动**

```bash
# 导入镜像
docker load -i guax-latest.tar

# 启动
docker compose up -d
```

> 极空间用户也可直接在 Docker 管理界面选择「导入镜像」上传 tar 文件。

## 项目结构

```
guax/
├── guax/
│   ├── __init__.py
│   ├── __main__.py           # 入口
│   ├── core/                 # 核心模块
│   │   ├── config.py         # 配置管理
│   │   ├── database.py       # 数据库
│   │   ├── logger.py         # 日志
│   │   └── models.py         # 数据模型
│   ├── scrapers/             # 刮削源
│   │   ├── base.py           # 基类
│   │   ├── source_a.py       # 数据源 A
│   │   ├── source_b.py       # 数据源 B
│   │   └── manager.py        # 管理器
│   ├── parsers/              # 解析器
│   │   └── filename_parser.py  # 文件名解析
│   ├── metadata/             # 元数据
│   │   └── generator.py      # NFO生成器
│   ├── api/                  # API路由
│   │   ├── scrape.py
│   │   ├── library.py
│   │   └── system.py
│   └── web/                  # Web界面
│       ├── app.py
│       └── templates/
│           └── index.html
├── config/
│   └── config.yaml           # 配置文件
├── data/                     # 数据目录
├── static/                   # 静态文件
├── tests/                    # 测试
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 使用示例

### API 刮削

```bash
# 刮削单个媒体
curl -X POST "http://localhost:8000/api/scrape" \
  -d "query=MD-001"

# 解析文件名
curl -X POST "http://localhost:8000/api/parse/filename" \
  -d "filename=MD-001-高清版.mp4"

# 列出刮削源
curl "http://localhost:8000/api/sources"
```

### Python SDK

```python
from guax.scrapers.manager import get_scraper_manager
from guax.parsers.chinese_adult import FilenameParser

# 初始化管理器
manager = get_scraper_manager()

# 解析文件名
parsed = manager.parse_filename("MD-001-高清.mp4")
print(f"番号: {parsed.code}")  # MD-001
print(f"平台: {parsed.platform}")  # MD

# 刮削
metadata = await manager.scrape("MD-001")
if metadata:
    print(f"标题: {metadata.title}")
    print(f"片商: {metadata.studio_zh}")
```

## 免责声明

本工具仅供个人学习研究使用，请勿用于商业用途或传播盗版资源。使用本工具产生的任何法律问题由使用者自行承担。

## 致谢

- [Amane](https://github.com/sqzw-x/amane) - 本项目的二创来源，AI 时代的私人影库
- 所有开源项目的贡献者

## License

MIT License - 详见 [LICENSE](LICENSE) 文件
