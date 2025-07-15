#!/bin/bash

# Aptos Task Manager - Dev部署脚本
# 基于官方文档: https://gushi10546.gitbook.io/aptos-kai-fa-zhe-wen-dang/kai-fa-zhe-jiao-cheng/ni-de-di-yi-ge-move-mo-kuai

set -e  # 错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
NETWORK="devnet"
FAUCET_URL="https://faucet.devnet.aptoslabs.com"
NODE_URL="https://fullnode.devnet.aptoslabs.com/v1"
PROFILE_NAME="task_manager_dev"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 错误处理函数
handle_error() {
    log_error "部署过程中发生错误: $1"
    log_error "请检查错误信息并重试"
    exit 1
}

# 检查依赖
check_dependencies() {
    log_step "检查依赖环境..."
    
    # 检查 Aptos CLI
    if ! command -v aptos &> /dev/null; then
        handle_error "Aptos CLI 未安装。请访问 https://aptos.dev/cli-tools/aptos-cli-tool/install-aptos-cli 安装"
    fi
    
    # 检查 jq
    if ! command -v jq &> /dev/null; then
        handle_error "jq 未安装。请使用您系统的包管理器安装 (例如: brew install jq)"
    fi
    
    # 检查版本
    local version=$(aptos --version | head -n1 | awk '{print $2}')
    log_info "发现 Aptos CLI 版本: $version"
    
    # 检查 Move.toml
    if [ ! -f "Move.toml" ]; then
        handle_error "Move.toml 文件不存在。请确保在项目根目录运行此脚本"
    fi
    
    log_info "依赖检查完成 ✓"
}

# 初始化 Aptos 配置
init_aptos_config() {
    log_step "初始化 Aptos 配置..."
    
    # 检查是否已存在配置
    if aptos config show-profiles | grep -q "$PROFILE_NAME"; then
        log_warn "配置文件 $PROFILE_NAME 已存在，将使用现有配置"
        return 0
    fi
    
    # 创建新的配置
    log_info "创建新的开发配置..."
    aptos init --profile $PROFILE_NAME \
        --network $NETWORK \
        --skip-faucet || handle_error "Aptos 初始化失败"
    
    log_info "Aptos 配置初始化完成 ✓"
}

# 获取账户地址
get_account_address() {
    local address
    address=$(aptos config show-profiles --profile $PROFILE_NAME | grep "account" | awk '{print $2}' | tr -d ',"')
    if [ -z "$address" ]; then
        handle_error "无法获取账户地址"
    fi
    echo $address
}

# 为账户充值
fund_account() {
    log_step "为开发账户充值..."
    
    local account_addr=$(get_account_address)
    log_info "账户地址: $account_addr"
    
    # 检查当前余额
    local balance
    balance=$(aptos account lookup-address --profile $PROFILE_NAME --address "$account_addr" 2>/dev/null | grep "apt_balance" | awk '{print $2}' || echo "0")
    if [ -z "$balance" ]; then
        balance=0
    fi
    log_info "当前余额: $balance APT"
    
    # 如果余额不足，从水龙头获取资金
    if [ "$balance" -lt 10000000 ]; then  # 0.1 APT
        log_info "余额不足，从水龙头获取资金..."
        aptos account fund-with-faucet --profile $PROFILE_NAME --account "$account_addr" --amount 100000000 || handle_error "账户充值失败"
        log_info "账户充值完成 ✓"
    else
        log_info "账户余额充足，跳过充值"
    fi
}

# 更新 Move.toml 中的地址
update_move_toml() {
    log_step "动态更新 Move.toml..."
    
    local account_addr
    account_addr=$(get_account_address)
    
    # 备份原文件
    cp Move.toml Move.toml.bak
    
    # 使用 sed 更新地址。注意MacOS和Linux的sed兼容性
    sed -i.bak "s/aptos_task_manager = \".*\"/aptos_task_manager = \"$account_addr\"/" Move.toml
    
    log_info "Move.toml 地址已更新为: $account_addr"
}

# 恢复 Move.toml
restore_move_toml() {
    if [ -f "Move.toml.bak" ]; then
        log_info "恢复 Move.toml..."
        mv Move.toml.bak Move.toml
    fi
}

# 编译合约
compile_contract() {
    log_step "编译 Move 合约..."
    
    # 清理之前的编译产物
    if [ -d "build" ]; then
        rm -rf build
        log_info "清理旧的编译产物"
    fi
    
    # 编译合约
    log_info "开始编译..."
    aptos move compile --save-metadata || handle_error "合约编译失败"
    
    log_info "合约编译成功 ✓"
    
    # 显示编译信息
    if [ -f "build/aptos_task_manager/package-metadata.bcs" ]; then
        local package_size=$(du -h build/aptos_task_manager/package-metadata.bcs | awk '{print $1}')
        log_info "包大小: $package_size"
    fi
}

# 运行单元测试
run_tests() {
    log_step "运行单元测试..."
    
    # 运行测试
    log_info "执行测试套件..."
    aptos move test --coverage || handle_error "单元测试失败"
    
    log_info "所有测试通过 ✓"
    
    # 显示覆盖率信息（如果可用）
    if [ -d "coverage" ]; then
        log_info "测试覆盖率报告已生成在 coverage/ 目录"
    fi
}

# 部署合约到链上
deploy_contract() {
    log_step "部署合约到 $NETWORK..."
    
    # 动态更新地址
    update_move_toml

    # 编译
    compile_contract

    # 检查是否已编译
    if [ ! -d "build" ]; then
        handle_error "合约未编译，请先运行编译步骤"
    fi
    
    # 发布合约
    log_info "发布合约到链上..."
    local deploy_output
    deploy_output=$(aptos move publish \
        --profile "$PROFILE_NAME" \
        --verbose \
        --assume-yes 2>&1)

    if [ $? -ne 0 ]; then
        log_error "部署输出: $deploy_output"
        handle_error "合约部署失败"
    fi
    
    # 提取交易信息
    local tx_hash
    tx_hash=$(echo "$deploy_output" | jq -r '.Result.transaction_hash')
    local gas_used
    gas_used=$(echo "$deploy_output" | jq -r '.Result.gas_used')

    if [ -z "$tx_hash" ] || [ "$tx_hash" == "null" ]; then
        log_error "无法从部署输出中提取交易哈希。CLI输出: $deploy_output"
        handle_error "交易哈希解析失败"
    fi
    
    log_info "合约部署成功 ✓"
    log_info "交易哈希: $tx_hash"
    log_info "消耗 Gas: $gas_used"
    
    # 验证部署
    log_info "验证合约部署状态 (轮询最多30秒)..."
    local end_time=$((SECONDS + 30))
    local tx_status=""
    while [ $SECONDS -lt $end_time ]; do
        tx_status=$(aptos transaction get --hash "$tx_hash" --profile "$PROFILE_NAME" 2>/dev/null || echo "")
        if echo "$tx_status" | grep -q '"success": true'; then
            log_info "交易确认成功！"
            break
        fi
        sleep 2
        echo -n "."
    done
    
    echo "" # Newline after polling dots

    if ! echo "$tx_status" | grep -q '"success": true'; then
        handle_error "部署交易确认失败或超时。交易详情:\n$tx_status"
    fi
    
    # 检查模块是否存在
    local account_addr
    account_addr=$(get_account_address)
    if aptos account list --profile $PROFILE_NAME --account "$account_addr" --query modules | grep -q "task_manager"; then
        log_info "合约模块验证成功 ✓"
    else
        log_warn "合约模块验证失败"
        handle_error "虽然交易成功，但在账户中未找到 task_manager 模块"
    fi
    
    # 恢复 Move.toml
    restore_move_toml
}

# 检查部署状态
check_deployment_status() {
    log_step "检查部署状态..."
    
    local account_addr=$(get_account_address)
    
    # 检查账户信息
    log_info "账户地址: $account_addr"
    
    # 检查余额
    local balance_output
    balance_output=$(aptos account lookup-address --profile $PROFILE_NAME --address "$account_addr" 2>/dev/null || echo "")
    if [ -n "$balance_output" ]; then
        local balance
        balance=$(echo "$balance_output" | grep "apt_balance" | awk '{print $2}' || echo "0")
        log_info "账户余额: $balance APT"
    fi
    
    # 检查已部署的模块
    log_info "检查已部署的模块..."
    local modules
    modules=$(aptos account list --profile $PROFILE_NAME --account "$account_addr" --query modules 2>/dev/null || echo "")
    if echo "$modules" | grep -q "task_manager"; then
        log_info "✓ task_manager 模块已部署"
    else
        log_warn "task_manager 模块未找到"
    fi
}

# -----------------------------------------------------------------------------
# 命令处理
# -----------------------------------------------------------------------------

# 显示帮助信息
usage() {
    echo "Aptos Task Manager - Dev 部署脚本"
    echo ""
    echo "用法: $0 {init|compile|test|deploy|all|status|help}"
    echo ""
    echo "命令:"
    echo "  init      检查依赖并初始化Aptos开发配置、为账户充值"
    echo "  compile   编译 Move 合约"
    echo "  test      运行单元测试"
    echo "  deploy    编译并部署合约到 $NETWORK"
    echo "  all       执行从初始化到部署的完整流程"
    echo "  status    检查账户和合约的部署状态"
    echo "  initialize-manager  为部署者账户初始化TaskManager资源"
    echo "  help      显示此帮助信息"
    echo ""
    exit 1
}

# 初始化环境
cmd_init() {
    log_step "==> Phase: 环境初始化"
    check_dependencies
    init_aptos_config
    fund_account
    echo ""
    log_info "基础环境准备完成！"
    log_info "账户地址: $(get_account_address)"
    log_info "网络: $NETWORK"
    log_info "配置文件: $PROFILE_NAME"
    log_step "==> Phase: 环境初始化完成 ✓"
}

# 调用initialize函数
cmd_initialize_manager() {
    log_step "==> Command: initialize-manager"
    local account_addr
    account_addr=$(get_account_address)
    local func_id="${account_addr}::task_manager::initialize"
    
    log_info "为账户 $account_addr 初始化 TaskManager..."
    log_info "执行: aptos move run --function-id $func_id"

    local exec_output
    exec_output=$(aptos move run \
        --function-id "$func_id" \
        --profile "$PROFILE_NAME" \
        --assume-yes 2>&1)
    
    if [ $? -ne 0 ]; then
        log_error "初始化失败: $exec_output"
        handle_error "执行 initialize 函数出错"
    fi

    # 简单的成功检查
    if echo "$exec_output" | grep -q '"success": true'; then
        log_info "TaskManager 初始化成功 ✓"
    else
        log_warn "未在输出中检测到明确的成功标志，请手动检查。输出: $exec_output"
    fi
    log_step "==> Command: initialize-manager 完成 ✓"
}

# 主函数
main() {
    if [ -z "$1" ]; then
        usage
    fi

    # 设置trap，确保脚本退出时恢复Move.toml
    trap restore_move_toml EXIT

    case "$1" in
        init)
            cmd_init
            ;;
        compile)
            log_step "==> Command: compile"
            compile_contract
            log_step "==> Command: compile 完成 ✓"
            ;;
        test)
            log_step "==> Command: test"
            run_tests
            log_step "==> Command: test 完成 ✓"
            ;;
        deploy)
            log_step "==> Command: deploy"
            deploy_contract
            log_step "==> Command: deploy 完成 ✓"
            ;;
        all)
            log_step "==> Command: all (全流程)"
            cmd_init
            run_tests
            deploy_contract
            cmd_initialize_manager
            check_deployment_status
            log_step "==> Command: all (全流程) 完成 ✓"
            ;;
        status)
            log_step "==> Command: status"
            check_deployment_status
            log_step "==> Command: status 完成 ✓"
            ;;
        initialize-manager)
            cmd_initialize_manager
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            log_error "无效命令: $1"
            usage
            ;;
    esac
}

# 错误陷阱
trap 'handle_error "脚本执行被中断"' INT TERM

# 如果脚本被直接执行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 