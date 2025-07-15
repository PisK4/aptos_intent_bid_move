#!/usr/bin/env python3
"""
Aptos Bidding System - 选择中标者脚本
Personal Agent 选择任务的中标者
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
    DEFAULT_PROFILE
)


async def select_winner(
    profile: str,
    platform_addr: str,
    task_id: str,
):
    """选择任务的中标者"""
    
    client, executor_account = await get_client_and_account(profile)
    executor_addr = str(executor_account.address())
    
    print("=" * 50)
    print("选择中标者")
    print("=" * 50)
    print(f"执行者: {executor_addr}")
    print(f"平台地址: {platform_addr}")
    print(f"任务 ID: {task_id}")
    print("")
    
    try:
        # 将任务ID转换为字节数组
        task_id_bytes = format_task_id(task_id)
        
        # 构建交易Payload
        payload = EntryFunction.natural(
            f"{platform_addr}::bidding_system",
            "select_winner",
            [], # 无类型参数
            [
                TransactionArgument(AccountAddress.from_str(platform_addr), Serializer.struct),
                TransactionArgument(task_id_bytes, Serializer.sequence_serializer(Serializer.u8)),
            ],
        )
        
        # 生成并签名交易
        signed_transaction = await client.create_bcs_signed_transaction(
            executor_account, TransactionPayload(payload)
        )
        
        # 提交交易
        txn_hash = await client.submit_bcs_transaction(signed_transaction)
        print(f"交易提交中... 哈希: {txn_hash}")
        
        # 等待交易确认
        await client.wait_for_transaction(txn_hash)
        tx_info = await client.transaction_by_hash(txn_hash)
        
        print(f"中标者选择成功! 交易版本: {tx_info['version']}")
        print("")
        print("已根据价格和声誉评分选择最佳竞标者。")
        print("中标者现在可以开始执行任务并在完成后调用 complete_task。")
        
        return True
        
    except Exception as e:
        print(f"选择中标者失败: {e}")
        return False
    finally:
        await client.close()


async def main():
    parser = argparse.ArgumentParser(description="选择任务的中标者")
    parser.add_argument("task_id", type=str, help="任务的唯一ID")
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
    if len(args.task_id.strip()) == 0:
        print("错误: 任务ID不能为空")
        return
    
    # 选择中标者
    success = await select_winner(
        args.profile,
        platform_addr,
        args.task_id,
    )
    
    if success:
        print("中标者选择完成!")
    else:
        print("中标者选择失败!")


if __name__ == "__main__":
    asyncio.run(main())