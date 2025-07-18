#!/bin/bash

# A2A-Aptos Service Agent 初始化脚本
# 用于解决 API 速率限制问题

set -e

echo "🚀 初始化 Service Agent Profile..."

# 加载环境变量
if [ -f .env ]; then
    source .env
    echo "✅ 已加载环境变量"
else
    echo "❌ 未找到 .env 文件"
    exit 1
fi

# 检查 API token
if [ -z "$FAUCET_AUTH_TOKEN" ]; then
    echo "❌ FAUCET_AUTH_TOKEN 未设置"
    exit 1
fi

echo "🔑 使用 API Token: ${FAUCET_AUTH_TOKEN:0:20}..."

# 尝试使用 API token 初始化
echo "📝 正在初始化 service_agent profile..."

# 方法1: 使用环境变量
export FAUCET_AUTH_TOKEN=$FAUCET_AUTH_TOKEN

# 方法2: 直接在命令中指定
aptos init --profile service_agent --network devnet --faucet-auth-token "$FAUCET_AUTH_TOKEN" --assume-yes

echo "✅ Service Agent Profile 初始化完成"

# 验证配置
echo "🔍 验证配置..."
aptos config show-profiles

echo "🎉 初始化完成！"