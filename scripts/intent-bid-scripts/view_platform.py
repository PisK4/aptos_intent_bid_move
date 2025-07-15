#!/usr/bin/env python3
"""
Aptos Bidding System - 平台统计脚本
查看平台整体统计信息
"""

import argparse
import asyncio
from common_bidding import (
    get_client_and_account, 
    get_platform_address,
    print_platform_stats,
    DEFAULT_PROFILE
)


async def view_platform_stats(
    profile: str,
    platform_addr: str,
):
    """查看平台统计信息"""
    
    client, account = await get_client_and_account(profile)
    
    print("=" * 50)
    print("平台统计信息")
    print("=" * 50)
    print(f"平台地址: {platform_addr}")
    print("")
    
    try:
        # 调用 get_platform_stats view 函数
        result = await client.view(
            f"{platform_addr}::bidding_system::get_platform_stats",
            [],
            [platform_addr]
        )
        
        if result:
            # 返回的是 (total_tasks, completed_tasks, cancelled_tasks) 元组
            stats = result  # 直接使用结果
            
            print("平台统计:")
            print("-" * 30)
            # 暂时直接打印原始数据
            print(f"原始统计数据: {stats}")
            print("")
            
            # 获取平台资源状态
            try:
                resource_type = f"{platform_addr}::bidding_system::BiddingPlatform"
                resources = await client.account_resources(platform_addr)
                
                platform_resource = None
                for resource in resources:
                    if resource['type'] == resource_type:
                        platform_resource = resource
                        break
                
                if platform_resource:
                    print("平台资源状态:")
                    print("-" * 30)
                    print("✓ BiddingPlatform 资源已初始化")
                    print(f"资源数据: {platform_resource['data']}")
                else:
                    print("⚠️ BiddingPlatform 资源未找到")
                    
            except Exception as e:
                print(f"获取平台资源状态失败: {e}")
        else:
            print("无法获取平台统计信息")
            return False
        
        return True
        
    except Exception as e:
        print(f"查询平台统计失败: {e}")
        return False
    finally:
        await client.close()


async def main():
    parser = argparse.ArgumentParser(description="查看平台统计信息")
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
    
    # 查看平台统计
    success = await view_platform_stats(args.profile, platform_addr)
    
    if success:
        print("平台统计查询完成!")
    else:
        print("平台统计查询失败!")


if __name__ == "__main__":
    asyncio.run(main())