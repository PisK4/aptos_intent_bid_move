#!/usr/bin/env python3
"""
Aptos Bidding System - 查看任务脚本
查询任务详细信息、竞标情况和状态
"""

import argparse
import asyncio
from common_bidding import (
    get_client_and_account, 
    get_platform_address,
    format_task_id,
    print_task_info,
    print_bid_info,
    DEFAULT_PROFILE
)


async def view_task(
    profile: str,
    platform_addr: str,
    task_id: str,
):
    """查看任务详细信息"""
    
    client, account = await get_client_and_account(profile)
    
    print("=" * 50)
    print("查看任务信息")
    print("=" * 50)
    print(f"平台地址: {platform_addr}")
    print(f"任务 ID: {task_id}")
    print("")
    
    try:
        # 将任务ID转换为十六进制格式
        task_id_hex = "0x" + task_id.encode('utf-8').hex()
        
        # 调用 get_task view 函数
        result = await client.view(
            f"{platform_addr}::bidding_system::get_task",
            [],
            [platform_addr, task_id_hex]
        )
        
        if result:
            # 假设返回的是任务结构体数据
            task_data = result  # 直接使用结果，不是第一个元素
            
            print("任务详细信息:")
            print("-" * 30)
            # 暂时直接打印原始数据，因为结构可能不同
            print(f"原始任务数据: {task_data}")
            print("")
            
            # 获取竞标信息
            bid_result = await client.view(
                f"{platform_addr}::bidding_system::get_task_bids",
                [],
                [platform_addr, task_id_hex]
            )
            
            if bid_result:
                bids = bid_result
                print(f"竞标信息: {bids}")
                print("")
            else:
                print("当前没有竞标信息")
        else:
            print("任务未找到")
            return False
        
        return True
        
    except Exception as e:
        print(f"查询任务失败: {e}")
        return False
    finally:
        await client.close()


async def check_task_exists(
    profile: str,
    platform_addr: str,
    task_id: str,
):
    """检查任务是否存在"""
    
    client, account = await get_client_and_account(profile)
    
    try:
        # 将任务ID转换为十六进制格式
        task_id_hex = "0x" + task_id.encode('utf-8').hex()
        
        # 调用 task_exists view 函数
        result = await client.view(
            f"{platform_addr}::bidding_system::task_exists",
            [],
            [platform_addr, task_id_hex]
        )
        
        exists = result if result else False
        print(f"任务 {task_id} 存在: {exists}")
        return exists
        
    except Exception as e:
        print(f"检查任务存在性失败: {e}")
        return False
    finally:
        await client.close()


async def main():
    parser = argparse.ArgumentParser(description="查看任务信息")
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
    parser.add_argument(
        "--check-exists",
        action="store_true",
        help="仅检查任务是否存在"
    )
    
    args = parser.parse_args()
    
    # 获取平台地址
    platform_addr = args.platform if args.platform else get_platform_address(DEFAULT_PROFILE)
    
    # 验证参数
    if len(args.task_id.strip()) == 0:
        print("错误: 任务ID不能为空")
        return
    
    # 执行查询
    if args.check_exists:
        await check_task_exists(args.profile, platform_addr, args.task_id)
    else:
        success = await view_task(args.profile, platform_addr, args.task_id)
        
        if success:
            print("任务查询完成!")
        else:
            print("任务查询失败!")


if __name__ == "__main__":
    asyncio.run(main())