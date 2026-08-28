@echo off
chcp 65001 >nul
setlocal

set IMAGE_NAME=guax
set IMAGE_TAG=latest
set OUTPUT_FILE=guax-%IMAGE_TAG%.tar

echo ========================================
echo   Guax Docker 镜像打包脚本
echo ========================================
echo.

REM 检查 docker 是否可用
docker --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 docker，请先安装 Docker Desktop
    pause
    exit /b 1
)

echo [1/3] 构建镜像...
docker build -t %IMAGE_NAME%:%IMAGE_TAG% .
if errorlevel 1 (
    echo [错误] 镜像构建失败
    pause
    exit /b 1
)

echo.
echo [2/3] 导出镜像为 tar...
docker save -o %OUTPUT_FILE% %IMAGE_NAME%:%IMAGE_TAG%
if errorlevel 1 (
    echo [错误] 镜像导出失败
    pause
    exit /b 1
)

echo.
echo [3/3] 完成！
echo.
echo 镜像已保存到: %CD%\%OUTPUT_FILE%
for %%I in (%OUTPUT_FILE%) do echo 文件大小: %%~zI 字节
echo.
echo ========================================
echo   接下来:
echo   1. 把 %OUTPUT_FILE% 和 docker-compose.yml 上传到 NAS
echo   2. 在 NAS 上执行: docker load -i %OUTPUT_FILE%
echo   3. 启动: docker compose up -d
echo ========================================
echo.
pause