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

# --- 核心函数 ---

def load_account_from_profile(profile: str) -> Account:
    """从 .aptos/config.yaml 中加载指定profile的账户"""
    
    # 优先使用项目本地的配置文件，然后是全局配置文件
    local_config_path = os.path.join(".aptos", "config.yaml")
    global_config_path = os.path.expanduser("~/.aptos/config.yaml")
    config_path = ""

    if os.path.exists(local_config_path):
        config_path = local_config_path
    elif os.path.exists(global_config_path):
        config_path = global_config_path
    else:
        raise FileNotFoundError(
            "Aptos config file not found in local ./.aptos/ or global ~/.aptos/"
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

if __name__ == '__main__':
    # 一个简单的测试，用于验证函数是否正常工作
    try:
        acc = load_account_from_profile(DEFAULT_PROFILE)
        print(f"成功加载配置文件 '{DEFAULT_PROFILE}'")
        print(f"账户地址: {acc.address()}")
    except (FileNotFoundError, ValueError) as e:
        print(f"错误: {e}") 