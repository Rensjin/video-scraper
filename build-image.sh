#!/bin/bash
set -e

IMAGE_NAME="guax"
IMAGE_TAG="latest"
OUTPUT_FILE="guax-${IMAGE_TAG}.tar"

echo "========================================"
echo "  Guax Docker 镜像打包脚本"
echo "========================================"
echo

# 检查 docker 是否可用
if ! command -v docker &> /dev/null; then
    echo "[错误] 未检测到 docker，请先安装 Docker"
    exit 1
fi

echo "[1/3] 构建镜像..."
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .

echo
echo "[2/3] 导出镜像为 tar..."
docker save -o "${OUTPUT_FILE}" "${IMAGE_NAME}:${IMAGE_TAG}"

echo
echo "[3/3] 完成！"
echo
echo "镜像已保存到: $(pwd)/${OUTPUT_FILE}"
ls -lh "${OUTPUT_FILE}"
echo
echo "========================================"
echo "  接下来:"
echo "  1. 把 ${OUTPUT_FILE} 和 docker-compose.yml 上传到 NAS"
echo "  2. 在 NAS 上执行: docker load -i ${OUTPUT_FILE}"
echo "  3. 启动: docker compose up -d"
echo "========================================"