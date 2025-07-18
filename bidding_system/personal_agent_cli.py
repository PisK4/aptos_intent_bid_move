#!/usr/bin/env python3
"""
A2A-Aptos Bidding System - Personal Agent CLI
Personal Agent 发布任务和管理竞标的命令行工具
"""

import argparse
import asyncio
import uuid
import os
import sys
from typing import Optional
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
    get_platform_address,
    format_task_id,
    format_amount,
    format_status,
    print_task_info,
    STATUS_NAMES,
    DEFAULT_PROFILE
)


class PersonalAgentCLI:
    """Personal Agent 命令行工具"""
    
    def __init__(self):
        # 加载环境变量
        load_dotenv()
        
        # 从环境变量或配置文件获取设置
        self.platform_address = os.getenv("PLATFORM_ADDRESS")
        self.personal_agent_profile = os.getenv("PERSONAL_AGENT_PROFILE", "personal_agent")
        self.service_agent_profile = os.getenv("SERVICE_AGENT_PROFILE", "service_agent")
        
        if not self.platform_address:
            print("错误: 请在 .env 文件中设置 PLATFORM_ADDRESS")
            sys.exit(1)
    
    async def initialize_platform(self):
        """初始化竞标平台"""
        print("=" * 50)
        print("初始化竞标平台")
        print("=" * 50)
        
        client, deployer_account = await get_client_and_account(self.personal_agent_profile)
        deployer_addr = str(deployer_account.address())
        
        print(f"部署者: {deployer_addr}")
        print(f"平台地址: {self.platform_address}")
        print("")
        
        try:
            # 构建交易Payload
            payload = EntryFunction.natural(
                f"{self.platform_address}::bidding_system",
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
            print(f"交易提交中... 哈希: {txn_hash}")
            
            # 等待交易确认
            await client.wait_for_transaction(txn_hash)
            tx_info = await client.transaction_by_hash(txn_hash)
            
            print(f"平台初始化成功! 交易版本: {tx_info['version']}")
            print("平台已准备就绪，可以开始发布任务。")
            
            return True
            
        except Exception as e:
            print(f"平台初始化失败: {e}")
            return False
        finally:
            await client.close()
    
    async def publish_task(self, task_id: str, description: str, max_budget: int, deadline_seconds: int):
        """发布任务"""
        print("=" * 50)
        print("发布任务到竞标平台")
        print("=" * 50)
        
        client, creator_account = await get_client_and_account(self.personal_agent_profile)
        creator_addr = str(creator_account.address())
        
        print(f"创建者: {creator_addr}")
        print(f"平台地址: {self.platform_address}")
        print(f"任务 ID: {task_id}")
        print(f"描述: {description}")
        print(f"最大预算: {format_amount(max_budget)}")
        print(f"截止时间: {deadline_seconds} 秒")
        print("")
        
        try:
            # 将任务ID转换为字节数组
            task_id_bytes = format_task_id(task_id)
            
            # 构建交易Payload
            payload = EntryFunction.natural(
                f"{self.platform_address}::bidding_system",
                "publish_task",
                [],
                [
                    TransactionArgument(AccountAddress.from_str(self.platform_address), Serializer.struct),
                    TransactionArgument(task_id_bytes, Serializer.sequence_serializer(Serializer.u8)),
                    TransactionArgument(description, Serializer.str),
                    TransactionArgument(max_budget, Serializer.u64),
                    TransactionArgument(deadline_seconds, Serializer.u64),
                ],
            )
            
            # 生成并签名交易
            signed_transaction = await client.create_bcs_signed_transaction(
                creator_account, TransactionPayload(payload)
            )
            
            # 提交交易
            txn_hash = await client.submit_bcs_transaction(signed_transaction)
            print(f"交易提交中... 哈希: {txn_hash}")
            
            # 等待交易确认
            await client.wait_for_transaction(txn_hash)
            tx_info = await client.transaction_by_hash(txn_hash)
            
            print(f"任务发布成功! 交易版本: {tx_info['version']}")
            print(f"资金已托管: {format_amount(max_budget)}")
            print("")
            print(f"==> 任务 '{task_id}' 已发布。请记下此ID用于后续操作。 <==")
            print("接下来服务提供商可以对该任务进行竞标。")
            
            return True
            
        except Exception as e:
            print(f"任务发布失败: {e}")
            return False
        finally:
            await client.close()
    
    async def select_winner(self, task_id: str):
        """选择中标者"""
        print("=" * 50)
        print("选择任务中标者")
        print("=" * 50)
        
        client, creator_account = await get_client_and_account(self.personal_agent_profile)
        creator_addr = str(creator_account.address())
        
        print(f"执行者: {creator_addr}")
        print(f"任务 ID: {task_id}")
        print("")
        
        try:
            # 构建交易Payload
            task_id_bytes = format_task_id(task_id)
            payload = EntryFunction.natural(
                f"{self.platform_address}::bidding_system",
                "select_winner",
                [],
                [
                    TransactionArgument(AccountAddress.from_str(self.platform_address), Serializer.struct),
                    TransactionArgument(task_id_bytes, Serializer.sequence_serializer(Serializer.u8)),
                ],
            )
            
            # 生成并签名交易
            signed_transaction = await client.create_bcs_signed_transaction(
                creator_account, TransactionPayload(payload)
            )
            
            # 提交交易
            txn_hash = await client.submit_bcs_transaction(signed_transaction)
            print(f"交易提交中... 哈希: {txn_hash}")
            
            # 等待交易确认
            await client.wait_for_transaction(txn_hash)
            tx_info = await client.transaction_by_hash(txn_hash)
            
            print(f"中标者选择成功! 交易版本: {tx_info['version']}")
            print("任务已分配给中标者。")
            
            return True
            
        except Exception as e:
            print(f"选择中标者失败: {e}")
            return False
        finally:
            await client.close()
    
    async def complete_task(self, task_id: str):
        """完成任务 (由Service Agent执行)"""
        print("=" * 50)
        print("完成任务")
        print("=" * 50)
        
        client, service_account = await get_client_and_account(self.service_agent_profile)
        service_addr = str(service_account.address())
        
        print(f"Service Agent: {service_addr}")
        print(f"任务 ID: {task_id}")
        print("")
        
        try:
            # 构建交易Payload
            task_id_bytes = format_task_id(task_id)
            payload = EntryFunction.natural(
                f"{self.platform_address}::bidding_system",
                "complete_task",
                [],
                [
                    TransactionArgument(AccountAddress.from_str(self.platform_address), Serializer.struct),
                    TransactionArgument(task_id_bytes, Serializer.sequence_serializer(Serializer.u8)),
                ],
            )
            
            # 生成并签名交易
            signed_transaction = await client.create_bcs_signed_transaction(
                service_account, TransactionPayload(payload)
            )
            
            # 提交交易
            txn_hash = await client.submit_bcs_transaction(signed_transaction)
            print(f"交易提交中... 哈希: {txn_hash}")
            
            # 等待交易确认
            await client.wait_for_transaction(txn_hash)
            tx_info = await client.transaction_by_hash(txn_hash)
            
            print(f"任务完成成功! 交易版本: {tx_info['version']}")
            print("资金已结算给Service Agent。")
            
            return True
            
        except Exception as e:
            print(f"完成任务失败: {e}")
            return False
        finally:
            await client.close()
    
    async def get_task_status(self, task_id: str):
        """查询任务状态"""
        print("=" * 50)
        print("查询任务状态")
        print("=" * 50)
        
        client, _ = await get_client_and_account(self.personal_agent_profile)
        
        try:
            # 获取 BiddingPlatform 资源
            resource_type = f"{self.platform_address}::bidding_system::BiddingPlatform"
            resource = await client.account_resource(
                AccountAddress.from_str(self.platform_address),
                resource_type
            )
            
            # 获取 tasks 表的句柄
            tasks_handle = resource["data"]["tasks"]["inner"]["buckets"]["inner"]["buckets"][0]["inner"]["kvs"][0]["key"]
            
            # 查询具体任务
            key_type = "vector<u8>"
            value_type = f"{self.platform_address}::bidding_system::Task"
            task_id_hex = task_id.encode('utf-8').hex()
            
            task_data = await client.get_table_item(
                tasks_handle,
                key_type,
                value_type,
                task_id_hex
            )
            
            print(f"任务 ID: {task_id}")
            print_task_info(task_data)
            
            # 显示竞标信息
            bids = task_data.get('bids', [])
            if bids:
                print(f"竞标数量: {len(bids)}")
                print("竞标列表:")
                for i, bid in enumerate(bids, 1):
                    print(f"  [{i}] 竞标者: {bid['bidder']}")
                    print(f"      报价: {format_amount(bid['price'])}")
                    print(f"      声誉: {bid['reputation_score']}")
                    print(f"      时间: {bid['timestamp']}")
                    print()
            else:
                print("竞标列表: 无竞标或已清空")
            
            return True
            
        except Exception as e:
            print(f"查询任务状态失败: {e}")
            return False
        finally:
            await client.close()


async def main():
    """主入口函数"""
    cli = PersonalAgentCLI()
    
    parser = argparse.ArgumentParser(
        description="A2A-Aptos Personal Agent CLI - 与竞标平台交互的工具"
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="可用的子命令")
    
    # 初始化平台
    subparsers.add_parser("init", help="初始化平台 (仅需在部署后执行一次)")
    
    # 发布任务
    p_publish = subparsers.add_parser("publish", help="发布一个新任务")
    p_publish.add_argument("description", type=str, help="任务的详细描述")
    p_publish.add_argument("--budget", type=int, required=True, 
                           help="最高预算 (单位: Octas, e.g., 100000000 代表 1 APT)")
    p_publish.add_argument("--deadline", type=int, default=3600,
                           help="竞标截止时间 (从当前开始的秒数，默认为3600秒)")
    p_publish.add_argument("--task-id", type=str,
                           help="任务ID (不指定则自动生成)")
    
    # 选择中标者
    p_select = subparsers.add_parser("select-winner", help="为任务选择一个中标者")
    p_select.add_argument("task_id", type=str, help="从 'publish' 命令获取的任务 ID")
    
    # 完成任务
    p_complete = subparsers.add_parser("complete", help="标记任务完成 (由中标的 Service Agent 执行)")
    p_complete.add_argument("task_id", type=str, help="任务 ID")
    
    # 查询状态
    p_status = subparsers.add_parser("status", help="查询任务的详细状态")
    p_status.add_argument("task_id", type=str, help="任务 ID")
    
    args = parser.parse_args()
    
    try:
        if args.command == "init":
            await cli.initialize_platform()
        elif args.command == "publish":
            task_id = args.task_id if args.task_id else f"task-{uuid.uuid4().hex[:8]}"
            await cli.publish_task(task_id, args.description, args.budget, args.deadline)
        elif args.command == "select-winner":
            await cli.select_winner(args.task_id)
        elif args.command == "complete":
            await cli.complete_task(args.task_id)
        elif args.command == "status":
            await cli.get_task_status(args.task_id)
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())