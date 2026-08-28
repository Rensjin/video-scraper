# NAS 部署指南

适用于极空间（Zspace）等无公网镜像拉取环境的 NAS。

## 思路

由于 NAS 通常无法访问外网 Docker 仓库，我们利用 GitHub Actions 在云端构建镜像并打包成 `tar`，下载后通过 `docker load` 导入到 NAS。

## 一次性部署

### 1. 获取镜像 tar 包

打开 GitHub Actions 页面：

```
https://github.com/Rensjin/video-scraper/actions/workflows/build-image.yml
```

点击 **Run workflow**，等待约 2-3 分钟构建完成。

在 workflow 运行详情页底部的 **Artifacts** 区域下载 `guax-image-tar`（约 80 MB）。

下载后是一个 zip 包，解压得到 `guax-image.tar`。

### 2. 上传到 NAS

把 `guax-image.tar` 上传到 NAS 上任意目录，例如 `/docker/guax/`。

可通过 SMB 共享盘、U盘、scp 等任意方式上传。

### 3. SSH 登录 NAS

极空间开启 SSH：控制台 → 系统设置 → 远程访问 → SSH。

```bash
ssh admin@<NAS_IP>
```

### 4. 创建项目目录

```bash
mkdir -p /docker/guax/{data,config,logs}
cd /docker/guax
```

### 5. 下载 docker-compose 文件

```bash
wget https://raw.githubusercontent.com/Rensjin/video-scraper/main/docker-compose.nas.yml -O docker-compose.yml
```

或者手动创建 `docker-compose.yml`，内容：

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

### 6. 导入镜像

```bash
docker load -i /path/to/guax-image.tar
```

> 路径替换成你上传 tar 包的实际位置。

确认导入：

```bash
docker images | grep guax
# 输出应类似：guax  latest  xxxxx  X days ago  XXXMB
```

### 7. 启动容器

```bash
docker compose up -d
```

查看状态：

```bash
docker compose ps
# 应显示 guax 状态为 Up
```

### 8. 验证访问

浏览器打开：

```
http://<NAS_IP>:8000
```

## 后续维护

### 查看日志

```bash
cd /docker/guax
docker compose logs -f
```

### 停止 / 重启

```bash
docker compose stop
docker compose restart
docker compose down
```

### 升级到新版本

1. GitHub 触发新构建并下载新的 `guax-image.tar`
2. 上传到 NAS
3. SSH 到 NAS 执行：

```bash
cd /docker/guax

# 停止并移除旧容器（数据卷保留）
docker compose down

# 移除旧镜像
docker rmi guax:latest

# 导入新镜像
docker load -i /path/to/guax-image.tar

# 启动
docker compose up -d
```

### 数据备份

需要备份的目录：

- `/docker/guax/data` — 抓取到的视频元数据
- `/docker/guax/config` — 应用配置
- `/docker/guax/logs` — 日志

建议定期复制到 NAS 其他位置或外接硬盘。

### 完全卸载

```bash
cd /docker/guax
docker compose down
docker rmi guax:latest
rm -rf /docker/guax
```

## 常见问题

### 端口 8000 已被占用

修改 `docker-compose.yml` 中端口映射：

```yaml
ports:
  - "8888:8000"   # 宿主机 8888 → 容器 8000
```

然后 `docker compose up -d`。

### 镜像导入失败（no space left）

清理旧镜像：

```bash
docker image prune -a
```

### 容器启动后无法访问

1. 确认容器在运行：`docker compose ps`
2. 确认端口已监听：`netstat -tlnp | grep 8000`
3. 检查 NAS 防火墙是否放行了 8000 端口
4. 极空间默认 Docker 网络与主机网络互通，无需特殊配置

### 磁盘写入权限问题

```bash
cd /docker/guax
chmod -R 777 data config logs
docker compose restart
```