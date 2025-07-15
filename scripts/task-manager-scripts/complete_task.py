import argparse
import asyncio
from aptos_sdk.bcs import Serializer
from aptos_sdk.account_address import AccountAddress
from aptos_sdk.transactions import (
    EntryFunction,
    TransactionPayload,
    TransactionArgument,
)
from common import get_client_and_account, DEFAULT_PROFILE

async def complete_task(
    profile: str,
    task_creator_addr: str,
    task_id: str,
):
    """构建并提交一个 complete_task 交易"""
    
    # 注意：此处加载的账户是服务方(service_agent)
    client, service_agent_account = await get_client_and_account(profile)
    
    print("正在完成任务...")
    print(f"  - 服务提供者 (Profile: {profile}): {service_agent_account.address()}")
    print(f"  - 任务创建者地址: {task_creator_addr}")
    print(f"  - 任务ID: {task_id}")

    # 将 task_id 字符串转换为字节数组
    task_id_bytes = task_id.encode('utf-8')

    payload = EntryFunction.natural(
        f"{task_creator_addr}::task_manager",
        "complete_task",
        [],
        [
            TransactionArgument(AccountAddress.from_str(task_creator_addr), Serializer.struct),
            TransactionArgument(task_id_bytes, Serializer.sequence_serializer(Serializer.u8)),
        ],
    )
    
    signed_transaction = await client.create_bcs_signed_transaction(
        service_agent_account, TransactionPayload(payload)
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
    parser = argparse.ArgumentParser(description="完成一个Aptos任务")
    parser.add_argument("task_creator_addr", type=str, help="任务创建者的地址")
    parser.add_argument("task_id", type=str, help="要完成的任务ID (字符串)")
    parser.add_argument(
        "--profile",
        required=True, # 强制要求指定profile，以明确服务方身份
        help="指定服务方(签名者)的Aptos CLI profile",
    )
    
    args = parser.parse_args()
    
    asyncio.run(
        complete_task(
            args.profile,
            args.task_creator_addr,
            args.task_id,
        )
    ) 