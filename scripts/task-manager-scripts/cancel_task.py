import argparse
import asyncio
from aptos_sdk.bcs import Serializer
from aptos_sdk.transactions import (
    EntryFunction,
    TransactionPayload,
    TransactionArgument,
)
from common import get_client_and_account, DEFAULT_PROFILE

async def cancel_task(
    profile: str,
    task_id: str,
):
    """构建并提交一个 cancel_task 交易"""
    
    client, task_agent_account = await get_client_and_account(profile)
    
    print("正在取消任务...")
    print(f"  - 任务创建者 (Profile: {profile}): {task_agent_account.address()}")
    print(f"  - 任务ID: {task_id}")

    # 将 task_id 字符串转换为字节数组
    task_id_bytes = task_id.encode('utf-8')

    payload = EntryFunction.natural(
        f"{task_agent_account.address()}::task_manager",
        "cancel_task",
        [],
        [
            TransactionArgument(task_id_bytes, Serializer.sequence_serializer(Serializer.u8)),
        ],
    )
    
    signed_transaction = await client.create_bcs_signed_transaction(
        task_agent_account, TransactionPayload(payload)
    )
    
    try:
        txn_hash = await client.submit_bcs_transaction(signed_transaction)
        print(f"交易提交中... 哈希: {txn_hash}")
        await client.wait_for_transaction(txn_hash)

        tx_info = await client.transaction_by_hash(txn_hash)
        print(f"交易成功! 版本: {tx_info['version']}")
    except Exception as e:
        print(f"交易失败: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="取消一个Aptos任务")
    parser.add_argument("task_id", type=str, help="要取消的任务ID (字符串)")
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        help=f"指定任务创建者(签名者)的Aptos CLI profile (默认: {DEFAULT_PROFILE})",
    )
    
    args = parser.parse_args()
    
    asyncio.run(
        cancel_task(
            args.profile,
            args.task_id,
        )
    ) 