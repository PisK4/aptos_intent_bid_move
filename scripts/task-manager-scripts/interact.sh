#!/bin/bash

# Aptos Task Manager - 合约交互脚本
set -e # 错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- 配置 ---
# 使用与部署脚本相同的Profile，确保我们与正确的账户和网络交互
DEFAULT_PROFILE_NAME="task_manager_dev"
PROFILE_NAME="" # 将在main函数中设置

# --- 日志与错误处理 ---
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }
handle_error() { log_error "$1"; exit 1; }

# --- 辅助函数 ---
# 检查依赖
check_dependencies() {
    if ! command -v aptos &>/dev/null; then handle_error "Aptos CLI 未安装"; fi
    if ! command -v jq &>/dev/null; then handle_error "jq 未安装 (brew install jq)"; fi
}

# 获取当前配置的账户地址 (默认的签名者)
get_signer_address() {
    local address
    address=$(aptos config show-profiles --profile "$PROFILE_NAME" | grep "account" | awk '{print $2}' | tr -d ',"')
    if [ -z "$address" ]; then handle_error "无法从配置文件 $PROFILE_NAME 获取账户地址"; fi
    echo "$address"
}

# 将字符串转换为十六进制字节数组格式 (用于 vector<u8>)
string_to_hex_bytes() {
    local input="$1"
    echo -n "$input" | od -An -tx1 | tr -d ' \n' | sed 's/^/0x/'
}

# --- 帮助信息 ---
usage() {
    echo "Aptos Task Manager 合约交互脚本"
    echo ""
    echo "用法: $0 <命令> [参数...]"
    echo ""
    echo "命令:"
    echo "  create <task_id> <service_agent> <amount_octas> <deadline_secs> <description>"
    echo "    => 创建一个新任务. "
    echo "       - task_id:       任务的唯一ID (字符串)"
    echo "       - service_agent: 服务提供者地址 (例: 0x...)"
    echo "       - amount_octas:  支付金额 (单位: Octas, 1 APT = 10^8 Octas)"
    echo "       - deadline_secs: 截止日期 (从现在开始的秒数)"
    echo "       - description:   任务描述 (字符串)"
    echo ""
    echo "  complete <task_creator_addr> <task_id>"
    echo "    => (由服务方)完成一个任务. 当前签名者必须是任务的服务方."
    echo ""
    echo "  cancel <task_id>"
    echo "    => (由任务创建者)取消一个任务."
    echo ""
    echo "  claim_refund <task_id>"
    echo "    => (由任务创建者)为已过期的任务申请退款."
    echo ""
    exit 1
}

# --- 命令实现 ---

# 创建任务
cmd_create_task() {
    if [ "$#" -ne 5 ]; then log_error "参数数量错误"; usage; fi
    local task_id="$1"
    local service_agent="$2"
    local amount="$3"
    local deadline="$4"
    local description="$5"
    local signer_addr
    signer_addr=$(get_signer_address)
    
    # 将 task_id 转换为十六进制字节数组
    local task_id_hex
    task_id_hex=$(string_to_hex_bytes "$task_id")
    
    log_step "正在创建任务..."
    log_info "任务创建者 (签名者): $signer_addr"
    log_info "任务 ID: $task_id (hex: $task_id_hex)"
    log_info "服务提供者: $service_agent"
    log_info "支付金额: $amount Octas"
    log_info "截止秒数: $deadline"
    log_info "任务描述: \"$description\""
    
    local func_id="${signer_addr}::task_manager::create_task"
    
    aptos move run --function-id "$func_id" \
        --args "hex:$task_id_hex" "address:$service_agent" "u64:$amount" "u64:$deadline" "string:$description" \
        --profile "$PROFILE_NAME"
}

# 完成任务
cmd_complete_task() {
    if [ "$#" -ne 2 ]; then log_error "参数数量错误"; usage; fi
    local task_creator_addr="$1"
    local task_id="$2"
    local signer_addr
    signer_addr=$(get_signer_address)

    # 将 task_id 转换为十六进制字节数组
    local task_id_hex
    task_id_hex=$(string_to_hex_bytes "$task_id")

    log_step "正在完成任务 $task_id..."
    log_info "任务创建者地址: $task_creator_addr"
    log_info "服务提供者 (签名者): $signer_addr"
    log_info "任务 ID: $task_id (hex: $task_id_hex)"

    local func_id="${task_creator_addr}::task_manager::complete_task"
    
    aptos move run --function-id "$func_id" \
        --args "address:$task_creator_addr" "hex:$task_id_hex" \
        --profile "$PROFILE_NAME"
}

# 取消任务
cmd_cancel_task() {
    if [ "$#" -ne 1 ]; then log_error "参数数量错误"; usage; fi
    local task_id="$1"
    local signer_addr
    signer_addr=$(get_signer_address)

    # 将 task_id 转换为十六进制字节数组
    local task_id_hex
    task_id_hex=$(string_to_hex_bytes "$task_id")

    log_step "正在取消任务 $task_id..."
    log_info "任务创建者 (签名者): $signer_addr"
    log_info "任务 ID: $task_id (hex: $task_id_hex)"

    local func_id="${signer_addr}::task_manager::cancel_task"
    
    aptos move run --function-id "$func_id" \
        --args "hex:$task_id_hex" \
        --profile "$PROFILE_NAME"
}

# 申请退款
cmd_claim_refund() {
    if [ "$#" -ne 1 ]; then log_error "参数数量错误"; usage; fi
    local task_id="$1"
    local signer_addr
    signer_addr=$(get_signer_address)

    # 将 task_id 转换为十六进制字节数组
    local task_id_hex
    task_id_hex=$(string_to_hex_bytes "$task_id")

    log_step "正在为任务 $task_id 申请退款..."
    log_info "任务创建者 (签名者): $signer_addr"
    log_info "任务 ID: $task_id (hex: $task_id_hex)"

    local func_id="${signer_addr}::task_manager::claim_expired_task_refund"
    
    aptos move run --function-id "$func_id" \
        --args "hex:$task_id_hex" \
        --profile "$PROFILE_NAME"
}


# --- 主分发器 ---
main() {
    check_dependencies
    
    # 允许通过 --profile 标志覆盖默认配置
    if [ "$1" == "--profile" ]; then
        if [ -z "$2" ]; then handle_error "--profile 标志需要一个参数"; fi
        PROFILE_NAME=$2
        log_warn "使用指定的配置文件: $PROFILE_NAME"
        shift 2 # 移除 --profile 和它的参数
    else
        PROFILE_NAME=$DEFAULT_PROFILE_NAME
    fi

    if [ -z "$1" ]; then
        usage
    fi
    
    local command=$1
    shift # 移除第一个参数 (命令)，剩下的都是函数的参数
    
    case "$command" in
        create)
            cmd_create_task "$@"
            ;;
        complete)
            cmd_complete_task "$@"
            ;;
        cancel)
            cmd_cancel_task "$@"
            ;;
        claim_refund)
            cmd_claim_refund "$@"
            ;;
        *)
            log_error "无效命令: $command"
            usage
            ;;
    esac

    log_info "命令 '$command' 执行完成。"
}

main "$@" 