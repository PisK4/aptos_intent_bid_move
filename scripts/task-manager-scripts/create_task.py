import argparse
import asyncio
from aptos_sdk.bcs import Serializer
from aptos_sdk.account_address import AccountAddress
from aptos_sdk.type_tag import TypeTag, StructTag
from aptos_sdk.transactions import (
    EntryFunction,
    TransactionPayload,
    TransactionArgument,
)
from common import get_client_and_account, DEFAULT_PROFILE

async def create_task(
    profile: str,
    task_id: str,
    service_agent: str,
    amount_octas: int,
    deadline_secs: int,
    description: str,
):
    """构建并提交一个 create_task 交易"""
    
    client, task_agent_account = await get_client_and_account(profile)
    
    print("正在创建任务...")
    print(f"  - Profile: {profile}")
    print(f"  - 任务创建者: {task_agent_account.address()}")
    print(f"  - 任务 ID: {task_id}")
    print(f"  - 服务提供者: {service_agent}")
    print(f"  - 支付金额: {amount_octas} Octas")
    print(f"  - 截止时间: {deadline_secs} 秒")
    print(f"  - 描述: '{description}'")

    # 将 task_id 字符串转换为字节数组
    task_id_bytes = task_id.encode('utf-8')

    # 1. 构建交易Payload
    payload = EntryFunction.natural(
        f"{task_agent_account.address()}::task_manager",
        "create_task",
        [], # 无 type arguments
        [
            TransactionArgument(task_id_bytes, Serializer.sequence_serializer(Serializer.u8)),
            TransactionArgument(AccountAddress.from_str(service_agent), Serializer.struct),
            TransactionArgument(amount_octas, Serializer.u64),
            TransactionArgument(deadline_secs, Serializer.u64),
            TransactionArgument(description, Serializer.str),
        ],
    )
    
    # 2. 生成并签名交易
    signed_transaction = await client.create_bcs_signed_transaction(
        task_agent_account, TransactionPayload(payload)
    )
    
    # 3. 提交交易
    try:
        txn_hash = await client.submit_bcs_transaction(signed_transaction)
        print(f"交易提交中... 哈希: {txn_hash}")
        await client.wait_for_transaction(txn_hash)
        
        # 为了获取版本号，我们需要在等待后再次查询交易
        tx_info = await client.transaction_by_hash(txn_hash)
        print(f"交易成功! 版本: {tx_info['version']}")
    except Exception as e:
        print(f"交易失败: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="创建一个新的Aptos任务")
    parser.add_argument("task_id", type=str, help="任务的唯一ID (字符串)")
    parser.add_argument("service_agent", type=str, help="服务提供者的地址")
    parser.add_argument("amount_octas", type=int, help="支付金额 (Octas)")
    parser.add_argument("deadline_secs", type=int, help="任务截止秒数")
    parser.add_argument("description", type=str, help="任务描述")
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        help=f"指定用于签名的Aptos CLI profile (默认: {DEFAULT_PROFILE})",
    )
    
    args = parser.parse_args()
    
    asyncio.run(
        create_task(
            args.profile,
            args.task_id,
            args.service_agent,
            args.amount_octas,
            args.deadline_secs,
            args.description,
        )
    ) 