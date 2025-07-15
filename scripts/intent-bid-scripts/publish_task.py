#!/usr/bin/env python3
"""
Aptos Bidding System - 发布任务脚本
Personal Agent 发布任务并托管资金
"""

import argparse
import asyncio
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
    DEFAULT_PROFILE
)


async def publish_task(
    profile: str,
    platform_addr: str,
    task_id: str,
    description: str,
    max_budget: int,
    deadline_seconds: int,
):
    """发布任务到竞标平台"""
    
    client, creator_account = await get_client_and_account(profile)
    creator_addr = str(creator_account.address())
    
    print("=" * 50)
    print("发布任务到竞标平台")
    print("=" * 50)
    print(f"创建者: {creator_addr}")
    print(f"平台地址: {platform_addr}")
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
            f"{platform_addr}::bidding_system",
            "publish_task",
            [], # 无类型参数
            [
                TransactionArgument(AccountAddress.from_str(platform_addr), Serializer.struct),
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
        print("接下来服务提供商可以对该任务进行竞标。")
        
        return True
        
    except Exception as e:
        print(f"任务发布失败: {e}")
        return False
    finally:
        await client.close()


async def main():
    parser = argparse.ArgumentParser(description="发布任务到竞标平台")
    parser.add_argument("task_id", type=str, help="任务的唯一ID")
    parser.add_argument("description", type=str, help="任务描述")
    parser.add_argument("max_budget", type=int, help="最大预算 (Octas)")
    parser.add_argument("deadline_seconds", type=int, help="截止时间 (秒)")
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        help=f"指定 Aptos CLI 配置文件 (默认: {DEFAULT_PROFILE})"
    )
    parser.add_argument(
        "--platform",
        help="平台地址 (默认从profile获取)"
    )
    
    args = parser.parse_args()
    
    # 获取平台地址
    platform_addr = args.platform if args.platform else get_platform_address(args.profile)
    
    # 验证参数
    if args.max_budget <= 0:
        print("错误: 最大预算必须大于0")
        return
    
    if args.deadline_seconds <= 0:
        print("错误: 截止时间必须大于0")
        return
    
    if len(args.task_id.strip()) == 0:
        print("错误: 任务ID不能为空")
        return
    
    # 发布任务
    success = await publish_task(
        args.profile,
        platform_addr,
        args.task_id,
        args.description,
        args.max_budget,
        args.deadline_seconds,
    )
    
    if success:
        print("任务发布完成!")
    else:
        print("任务发布失败!")


if __name__ == "__main__":
    asyncio.run(main())