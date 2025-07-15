"""
Aptos Bidding System - 通用模块
基于 bidding_system.move 的 Python SDK 辅助工具
"""

import yaml
import os
from aptos_sdk.async_client import RestClient
from aptos_sdk.account import Account

# --- 配置 ---

# Devnet的节点和Faucet URL
NODE_URL = "https://fullnode.devnet.aptoslabs.com/v1"
FAUCET_URL = "https://faucet.devnet.aptoslabs.com"

# 默认的配置文件路径
DEFAULT_PROFILE = "task_manager_dev"

# bidding_system 模块名称
BIDDING_MODULE = "bidding_system"

# 任务状态常量
STATUS_PUBLISHED = 1
STATUS_ASSIGNED = 2
STATUS_COMPLETED = 3
STATUS_CANCELLED = 4

# 状态名称映射
STATUS_NAMES = {
    STATUS_PUBLISHED: "PUBLISHED",
    STATUS_ASSIGNED: "ASSIGNED", 
    STATUS_COMPLETED: "COMPLETED",
    STATUS_CANCELLED: "CANCELLED"
}

# --- 核心函数 ---

def load_account_from_profile(profile: str) -> Account:
    """从 .aptos/config.yaml 中加载指定profile的账户"""
    
    # 优先使用项目本地的配置文件，然后是全局配置文件
    # 查找项目根目录的 .aptos 配置
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, "..", "..")  # 回到项目根目录
    local_config_path = os.path.join(project_root, ".aptos", "config.yaml")
    
    # 也检查当前目录的 .aptos 配置
    current_config_path = os.path.join(".aptos", "config.yaml")
    global_config_path = os.path.expanduser("~/.aptos/config.yaml")
    
    config_path = ""

    if os.path.exists(local_config_path):
        config_path = local_config_path
    elif os.path.exists(current_config_path):
        config_path = current_config_path
    elif os.path.exists(global_config_path):
        config_path = global_config_path
    else:
        raise FileNotFoundError(
            f"Aptos config file not found in:\n"
            f"  - Project root: {local_config_path}\n"
            f"  - Current dir: {current_config_path}\n" 
            f"  - Global: {global_config_path}\n"
            f"Please run 'aptos init' to create configuration."
        )

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    if "profiles" not in config or profile not in config["profiles"]:
        raise ValueError(f"Profile '{profile}' not found in aptos config file.")

    private_key = config["profiles"][profile].get("private_key")
    if not private_key:
        raise ValueError(f"Private key not found for profile '{profile}'.")
        
    return Account.load_key(private_key)


async def get_client_and_account(profile: str = DEFAULT_PROFILE) -> tuple[RestClient, Account]:
    """
    创建一个Aptos REST客户端并从指定的配置文件加载账户。
    
    返回:
        一个元组 (RestClient, Account)
    """
    client = RestClient(NODE_URL)
    account = load_account_from_profile(profile)
    return client, account


def get_platform_address(profile: str = DEFAULT_PROFILE) -> str:
    """获取平台地址（从配置文件中获取账户地址）"""
    account = load_account_from_profile(profile)
    return str(account.address())


def get_function_id(platform_addr: str, function_name: str) -> str:
    """构造函数ID"""
    return f"{platform_addr}::{BIDDING_MODULE}::{function_name}"


def format_task_id(task_id: str) -> bytes:
    """将字符串任务ID转换为字节数组"""
    return task_id.encode('utf-8')


def format_status(status: int) -> str:
    """格式化状态显示"""
    return STATUS_NAMES.get(status, f"UNKNOWN({status})")


def format_amount(amount_octas: int) -> str:
    """格式化金额显示（Octas转APT）"""
    apt_amount = amount_octas / 100_000_000
    return f"{apt_amount:.8f} APT ({amount_octas} Octas)"


def print_task_info(task_data: dict):
    """打印任务信息"""
    print(f"任务 ID: {task_data.get('id', 'N/A')}")
    print(f"创建者: {task_data.get('creator', 'N/A')}")
    print(f"描述: {task_data.get('description', 'N/A')}")
    print(f"最大预算: {format_amount(task_data.get('max_budget', 0))}")
    print(f"截止时间: {task_data.get('deadline', 'N/A')}")
    print(f"状态: {format_status(task_data.get('status', 0))}")
    print(f"创建时间: {task_data.get('created_at', 'N/A')}")
    
    if task_data.get('winner') and task_data.get('winner') != "0x0":
        print(f"中标者: {task_data.get('winner')}")
        print(f"中标价格: {format_amount(task_data.get('winning_price', 0))}")
    
    if task_data.get('completed_at', 0) > 0:
        print(f"完成时间: {task_data.get('completed_at')}")


def print_bid_info(bid_data: dict):
    """打印竞标信息"""
    print(f"竞标者: {bid_data.get('bidder', 'N/A')}")
    print(f"报价: {format_amount(bid_data.get('price', 0))}")
    print(f"声誉评分: {bid_data.get('reputation_score', 0)}")
    print(f"提交时间: {bid_data.get('timestamp', 'N/A')}")


def print_platform_stats(stats: tuple):
    """打印平台统计信息"""
    total_tasks, completed_tasks, cancelled_tasks = stats
    print(f"总任务数: {total_tasks}")
    print(f"已完成任务: {completed_tasks}")
    print(f"已取消任务: {cancelled_tasks}")
    print(f"成功率: {(completed_tasks / total_tasks * 100) if total_tasks > 0 else 0:.2f}%")


if __name__ == '__main__':
    # 简单的测试，验证配置加载
    try:
        account = load_account_from_profile(DEFAULT_PROFILE)
        print(f"成功加载配置文件 '{DEFAULT_PROFILE}'")
        print(f"账户地址: {account.address()}")
        print(f"平台地址: {get_platform_address()}")
    except (FileNotFoundError, ValueError) as e:
        print(f"错误: {e}")