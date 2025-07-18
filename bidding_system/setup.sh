#!/bin/bash

# A2A-Aptos Bidding System 快速设置脚本

set -e  # 遇到错误时退出

echo "==========================================="
echo "A2A-Aptos Bidding System 快速设置"
echo "==========================================="

# 检查是否在正确目录
if [ ! -f "requirements.txt" ]; then
    echo "错误: 请在 bidding_system 目录下运行此脚本"
    exit 1
fi

# 步骤1: 安装Python依赖
echo "步骤1: 安装Python依赖..."
if command -v uv &> /dev/null; then
    echo "使用 uv 安装依赖..."
    uv sync
else
    echo "使用 pip 安装依赖..."
    pip install -r requirements.txt
fi

# 步骤2: 复制环境变量模板
echo "步骤2: 设置环境变量..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "已创建 .env 文件，请编辑并填入实际值"
else
    echo ".env 文件已存在，跳过"
fi

# 步骤3: 检查Aptos CLI
echo "步骤3: 检查Aptos CLI..."
if ! command -v aptos &> /dev/null; then
    echo "错误: 未找到 aptos CLI，请先安装 Aptos CLI"
    echo "安装说明: https://aptos.dev/cli-tools/aptos-cli-tool/install-aptos-cli"
    exit 1
fi

# 步骤4: 设置账户
echo "步骤4: 设置Aptos账户..."
echo "请按照以下步骤创建账户："
echo ""
echo "1. 创建部署者账户:"
echo "   aptos init --profile task_manager_dev --network devnet"
echo ""
echo "2. 创建Personal Agent账户:"
echo "   aptos init --profile personal_agent --network devnet"
echo ""
echo "3. 创建Service Agent账户:"
echo "   aptos init --profile service_agent --network devnet"
echo ""
echo "4. 为账户申请测试币:"
echo "   aptos account fund-with-faucet --profile task_manager_dev"
echo "   aptos account fund-with-faucet --profile personal_agent"
echo "   aptos account fund-with-faucet --profile service_agent"
echo ""

read -p "是否已完成账户设置? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "请先完成账户设置，然后重新运行此脚本"
    exit 1
fi

# 步骤5: 编译和部署合约
echo "步骤5: 编译和部署智能合约..."
cd ..
echo "编译合约..."
aptos move compile

echo "部署合约..."
aptos move publish --profile task_manager_dev

# 获取部署者地址
DEPLOYER_ADDRESS=$(aptos account list --profile task_manager_dev | grep "Result:" | awk '{print $2}')
echo "部署者地址: $DEPLOYER_ADDRESS"

# 步骤6: 初始化平台
echo "步骤6: 初始化平台..."
cd bidding_system
python deploy_system.py --initialize-only --profile task_manager_dev

# 步骤7: 更新环境变量
echo "步骤7: 更新环境变量..."
if [ -n "$DEPLOYER_ADDRESS" ]; then
    # 使用sed更新.env文件中的PLATFORM_ADDRESS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/PLATFORM_ADDRESS=.*/PLATFORM_ADDRESS=$DEPLOYER_ADDRESS/" .env
    else
        # Linux
        sed -i "s/PLATFORM_ADDRESS=.*/PLATFORM_ADDRESS=$DEPLOYER_ADDRESS/" .env
    fi
    echo "已更新 .env 文件中的 PLATFORM_ADDRESS"
else
    echo "警告: 无法获取部署者地址，请手动更新 .env 文件"
fi

echo ""
echo "==========================================="
echo "✅ 设置完成!"
echo "==========================================="
echo ""
echo "下一步操作："
echo "1. 验证 .env 文件中的配置"
echo "2. 启动Service Agent监控服务："
echo "   python service_agent_monitor.py"
echo "3. 在另一个终端中使用Personal Agent CLI："
echo "   python personal_agent_cli.py publish \"测试任务\" --budget 50000000"
echo ""
echo "查看完整使用说明: cat README.md"