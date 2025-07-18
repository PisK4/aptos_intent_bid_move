#!/usr/bin/env python3
"""
A2A-Aptos Bidding System - 部署和初始化脚本
部署智能合约并初始化平台
"""

import asyncio
import argparse
import os
import sys
from dotenv import load_dotenv
from aptos_sdk.bcs import Serializer
from aptos_sdk.account_address import AccountAddress
from aptos_sdk.transactions import (
    EntryFunction,
    TransactionPayload,
    TransactionArgument,
)
from common_bidding import (
    get_client_and_account,
    DEFAULT_PROFILE
)


class BiddingSystemDeployer:
    """竞标系统部署器"""
    
    def __init__(self, profile: str = DEFAULT_PROFILE):
        self.profile = profile
        load_dotenv()
        
    async def deploy_and_initialize(self):
        """部署合约并初始化平台"""
        print("=" * 60)
        print("A2A-Aptos Bidding System 部署与初始化")
        print("=" * 60)
        
        try:
            client, deployer_account = await get_client_and_account(self.profile)
            deployer_addr = str(deployer_account.address())
            
            print(f"部署者地址: {deployer_addr}")
            print(f"配置文件: {self.profile}")
            print("")
            
            # 步骤1: 检查账户余额
            print("步骤1: 检查账户余额")
            balance = await client.account_balance(deployer_addr)
            print(f"账户余额: {balance / 100_000_000:.8f} APT")
            
            if balance < 1_000_000:  # 少于0.01 APT
                print("警告: 账户余额较低，建议先申请测试币")
                print("运行: aptos account fund-with-faucet --profile your_profile")
                print("")
            
            # 步骤2: 编译合约
            print("步骤2: 编译智能合约")
            print("请确保已在项目根目录运行: aptos move compile")
            print("")
            
            # 步骤3: 部署合约
            print("步骤3: 部署智能合约")
            print("请确保已在项目根目录运行: aptos move publish --profile your_profile")
            print("")
            
            # 步骤4: 初始化平台
            print("步骤4: 初始化竞标平台")
            success = await self.initialize_platform(client, deployer_account, deployer_addr)
            
            if success:
                print("=" * 60)
                print("✅ 部署和初始化完成!")
                print("=" * 60)
                print(f"平台地址: {deployer_addr}")
                print("")
                print("下一步操作:")
                print("1. 将平台地址添加到 .env 文件中的 PLATFORM_ADDRESS")
                print("2. 创建 Personal Agent 和 Service Agent 账户")
                print("3. 为账户申请测试币")
                print("4. 启动监控服务和CLI工具")
                print("")
                print("示例 .env 配置:")
                print(f"PLATFORM_ADDRESS={deployer_addr}")
                print("PERSONAL_AGENT_PROFILE=personal_agent")
                print("SERVICE_AGENT_PROFILE=service_agent")
                
            else:
                print("❌ 初始化失败")
                
        except Exception as e:
            print(f"部署失败: {e}")
            return False
        finally:
            await client.close()
            
        return True
    
    async def initialize_platform(self, client, deployer_account, deployer_addr: str) -> bool:
        """初始化平台"""
        try:
            # 构建交易Payload
            payload = EntryFunction.natural(
                f"{deployer_addr}::bidding_system",
                "initialize",
                [],
                [
                    TransactionArgument(AccountAddress.from_str(deployer_addr), Serializer.struct),
                ],
            )
            
            # 生成并签名交易
            signed_transaction = await client.create_bcs_signed_transaction(
                deployer_account, TransactionPayload(payload)
            )
            
            # 提交交易
            txn_hash = await client.submit_bcs_transaction(signed_transaction)
            print(f"初始化交易提交中... 哈希: {txn_hash}")
            
            # 等待交易确认
            await client.wait_for_transaction(txn_hash)
            tx_info = await client.transaction_by_hash(txn_hash)
            
            print(f"✅ 平台初始化成功! 交易版本: {tx_info['version']}")
            return True
            
        except Exception as e:
            print(f"❌ 平台初始化失败: {e}")
            return False


async def setup_accounts():
    """设置账户的辅助函数"""
    print("=" * 60)
    print("账户设置指南")
    print("=" * 60)
    
    print("1. 创建部署者账户（通常为task_manager_dev）:")
    print("   aptos init --profile task_manager_dev --network devnet")
    print("")
    
    print("2. 创建Personal Agent账户:")
    print("   aptos init --profile personal_agent --network devnet")
    print("")
    
    print("3. 创建Service Agent账户:")
    print("   aptos init --profile service_agent --network devnet")
    print("")
    
    print("4. 为所有账户申请测试币:")
    print("   aptos account fund-with-faucet --profile task_manager_dev")
    print("   aptos account fund-with-faucet --profile personal_agent")
    print("   aptos account fund-with-faucet --profile service_agent")
    print("")
    
    print("5. 编译和部署合约:")
    print("   aptos move compile")
    print("   aptos move publish --profile task_manager_dev")
    print("")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="A2A-Aptos Bidding System 部署工具")
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        help=f"指定 Aptos CLI 配置文件 (默认: {DEFAULT_PROFILE})"
    )
    parser.add_argument(
        "--setup-accounts",
        action="store_true",
        help="显示账户设置指南"
    )
    parser.add_argument(
        "--initialize-only",
        action="store_true",
        help="仅初始化平台（假设合约已部署）"
    )
    
    args = parser.parse_args()
    
    if args.setup_accounts:
        await setup_accounts()
        return
    
    deployer = BiddingSystemDeployer(args.profile)
    
    if args.initialize_only:
        # 仅初始化平台
        try:
            client, deployer_account = await get_client_and_account(args.profile)
            deployer_addr = str(deployer_account.address())
            
            print(f"正在初始化平台... 部署者: {deployer_addr}")
            success = await deployer.initialize_platform(client, deployer_account, deployer_addr)
            
            if success:
                print("✅ 平台初始化完成!")
            else:
                print("❌ 平台初始化失败!")
                
            await client.close()
            
        except Exception as e:
            print(f"初始化失败: {e}")
            sys.exit(1)
    else:
        # 完整部署流程
        await deployer.deploy_and_initialize()


if __name__ == "__main__":
    asyncio.run(main())