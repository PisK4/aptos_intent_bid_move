#!/usr/bin/env python3
"""
Aptos Bidding System - 竞标脚本
Service Agent 对发布的任务进行竞标
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


async def place_bid(
    profile: str,
    platform_addr: str,
    task_id: str,
    bid_price: int,
    reputation_score: int,
):
    """对任务进行竞标"""
    
    client, bidder_account = await get_client_and_account(profile)
    bidder_addr = str(bidder_account.address())
    
    print("=" * 50)
    print("提交竞标")
    print("=" * 50)
    print(f"竞标者: {bidder_addr}")
    print(f"平台地址: {platform_addr}")
    print(f"任务 ID: {task_id}")
    print(f"竞标价格: {format_amount(bid_price)}")
    print(f"声誉评分: {reputation_score}")
    print("")
    
    try:
        # 将任务ID转换为字节数组
        task_id_bytes = format_task_id(task_id)
        
        # 构建交易Payload
        payload = EntryFunction.natural(
            f"{platform_addr}::bidding_system",
            "place_bid",
            [], # 无类型参数
            [
                TransactionArgument(AccountAddress.from_str(platform_addr), Serializer.struct),
                TransactionArgument(task_id_bytes, Serializer.sequence_serializer(Serializer.u8)),
                TransactionArgument(bid_price, Serializer.u64),
                TransactionArgument(reputation_score, Serializer.u64),
            ],
        )
        
        # 生成并签名交易
        signed_transaction = await client.create_bcs_signed_transaction(
            bidder_account, TransactionPayload(payload)
        )
        
        # 提交交易
        txn_hash = await client.submit_bcs_transaction(signed_transaction)
        print(f"交易提交中... 哈希: {txn_hash}")
        
        # 等待交易确认
        await client.wait_for_transaction(txn_hash)
        tx_info = await client.transaction_by_hash(txn_hash)
        
        print(f"竞标提交成功! 交易版本: {tx_info['version']}")
        print(f"竞标价格: {format_amount(bid_price)}")
        print("")
        print("等待任务创建者选择中标者...")
        
        return True
        
    except Exception as e:
        print(f"竞标失败: {e}")
        return False
    finally:
        await client.close()


async def main():
    parser = argparse.ArgumentParser(description="对任务进行竞标")
    parser.add_argument("task_id", type=str, help="任务的唯一ID")
    parser.add_argument("bid_price", type=int, help="竞标价格 (Octas)")
    parser.add_argument("reputation_score", type=int, help="声誉评分 (0-100)")
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
    platform_addr = args.platform if args.platform else get_platform_address(DEFAULT_PROFILE)
    
    # 验证参数
    if args.bid_price <= 0:
        print("错误: 竞标价格必须大于0")
        return
    
    if args.reputation_score < 0 or args.reputation_score > 100:
        print("错误: 声誉评分必须在0-100之间")
        return
    
    if len(args.task_id.strip()) == 0:
        print("错误: 任务ID不能为空")
        return
    
    print(f"args.profile: {args.profile}")
    print(f"platform_addr: {platform_addr}")
    
    # 提交竞标
    success = await place_bid(
        args.profile,
        platform_addr,
        args.task_id,
        args.bid_price,
        args.reputation_score,
    )
    
    if success:
        print("竞标提交完成!")
    else:
        print("竞标提交失败!")


if __name__ == "__main__":
    asyncio.run(main())