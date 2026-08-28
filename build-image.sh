#!/bin/bash
# ============================================================
# 极空间 / 群晖 / 通用 NAS 一键打包脚本
# 用法：
#   1. 在本地（已装 Docker 的机器）执行 ./build-image.sh
#   2. 把生成的 guax-latest.tar 传到 NAS
#   3. 在 NAS 上执行 docker load -i guax-latest.tar
# ============================================================

set -e

IMAGE_NAME="guax"
IMAGE_TAG="latest"
OUTPUT_FILE="${IMAGE_NAME}-${IMAGE_TAG}.tar"

echo "==> 1. 构建 Docker 镜像..."
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .

echo "==> 2. 导出镜像为 tar 包..."
docker save -o "${OUTPUT_FILE}" "${IMAGE_NAME}:${IMAGE_TAG}"

echo "==> 3. 完成！"
echo ""
echo "镜像文件：$(pwd)/${OUTPUT_FILE}"
ls -lh "${OUTPUT_FILE}"
echo ""
echo "==> NAS 上使用方式："
echo "  1. 把 ${OUTPUT_FILE} 拷贝到 NAS（比如 /data/Docker/guax/）"
echo "  2. SSH 登录 NAS，执行："
echo "       cd /data/Docker/guax"
echo "       docker load -i ${OUTPUT_FILE}"
echo "       docker compose up -d"
