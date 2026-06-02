#!/usr/bin/env bash
# backup.sh — 将 backup_ver 之外的所有文件打包压缩，保存到 backup_ver/
# 用法: ./backup.sh [排除目录1,排除目录2,...]
# 示例: ./backup.sh output,pretags-draw/output

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_NAME="$(basename "$SCRIPT_DIR")"
BACKUP_DIR="${SCRIPT_DIR}/backup_ver"

# 日期戳
TIMESTAMP="$(date +%Y%m%d)"
ARCHIVE_NAME="${PROJECT_NAME}-o-backup-${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="${BACKUP_DIR}/${ARCHIVE_NAME}"

# 如果同一天已有备份，追加时间戳避免覆盖
if [[ -f "${ARCHIVE_PATH}" ]]; then
    TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
    ARCHIVE_NAME="${PROJECT_NAME}-o-backup-${TIMESTAMP}.tar.gz"
    ARCHIVE_PATH="${BACKUP_DIR}/${ARCHIVE_NAME}"
fi

# 确保 backup_ver 目录存在
mkdir -p "${BACKUP_DIR}"

# 构建排除列表
EXCLUDES=(
    --exclude="./backup_ver"
    --exclude="./.git"
)

# 用户自定义排除（逗号分隔）
if [[ $# -ge 1 && -n "$1" ]]; then
    IFS=',' read -ra USER_EXCLUDES <<< "$1"
    for ex in "${USER_EXCLUDES[@]}"; do
        EXCLUDES+=(--exclude="./${ex}")
    done
fi

echo "📦 备份项目: ${PROJECT_NAME}"
echo "📁 排除项:   ${EXCLUDES[*]}"
echo "💾 目标文件: ${ARCHIVE_PATH}"
echo ""

# 打包压缩
tar czf "${ARCHIVE_PATH}" \
    -C "${SCRIPT_DIR}" \
    "${EXCLUDES[@]}" \
    .

# 结果
FILE_SIZE="$(du -h "${ARCHIVE_PATH}" | cut -f1)"
echo ""
echo "✅ 备份完成!"
echo "   文件: ${ARCHIVE_PATH}"
echo "   大小: ${FILE_SIZE}"
