@echo off
REM ============================================================
REM Windows 一键打包脚本（需要在已装 Docker Desktop 的机器上执行）
REM ============================================================

set IMAGE_NAME=guax
set IMAGE_TAG=latest
set OUTPUT_FILE=%IMAGE_NAME%-%IMAGE_TAG%.tar

echo ==^> 1. 构建 Docker 镜像...
docker build -t %IMAGE_NAME%:%IMAGE_TAG% .

echo.
echo ==^> 2. 导出镜像为 tar 包...
docker save -o %OUTPUT_FILE% %IMAGE_NAME%:%IMAGE_TAG%

echo.
echo ==^> 3. 完成！
echo 镜像文件：%CD%\%OUTPUT_FILE%
dir %OUTPUT_FILE%

echo.
echo ==^> NAS 上使用方式：
echo   1. 把 %OUTPUT_FILE% 拷贝到 NAS（比如 /data/Docker/guax/）
echo   2. SSH 登录 NAS，执行：
echo        cd /data/Docker/guax
echo        docker load -i %OUTPUT_FILE%
echo        docker compose up -d
