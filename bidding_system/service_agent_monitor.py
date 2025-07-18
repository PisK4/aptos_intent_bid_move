#!/usr/bin/env python3
"""
A2A-Aptos Bidding System - Service Agent 监控服务
自动监控新任务并进行竞标的后台服务
"""

import time
import requests
import json
import os
import asyncio
import sys
import signal
from typing import Dict, List, Optional
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
    format_task_id,
    format_amount,
    DEFAULT_PROFILE
)

# 全局停止事件
shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\n收到信号 {signum}，正在优雅停止服务...")
    shutdown_event.set()


class ServiceAgentMonitor:
    """Service Agent 监控和竞标服务"""
    
    def __init__(self):
        # 加载环境变量
        load_dotenv()
        
        # 从环境变量获取配置
        self.platform_address = os.getenv("PLATFORM_ADDRESS")
        self.node_url = os.getenv("APTOS_NODE_URL", "https://fullnode.devnet.aptoslabs.com/v1")
        self.indexer_url = os.getenv("APTOS_INDEXER_URL", "https://api.devnet.aptoslabs.com/v1/graphql")
        self.service_agent_profile = os.getenv("SERVICE_AGENT_PROFILE", "service_agent")
        
        # 监控配置
        self.poll_interval = int(os.getenv("MONITOR_POLL_INTERVAL", 30))
        self.bid_price_ratio = float(os.getenv("BID_PRICE_RATIO", 0.8))
        self.reputation_score = int(os.getenv("SERVICE_AGENT_REPUTATION", 90))
        
        # 状态文件
        self.state_file = "monitor_state.json"
        
        # 事件类型
        self.event_type = f"{self.platform_address}::bidding_system::TaskPublishedEvent"
        
        # 验证必要配置
        if not self.platform_address:
            print("错误: 请在 .env 文件中设置 PLATFORM_ADDRESS")
            sys.exit(1)
        
        print("--- Service Agent 监控服务初始化 ---")
        print(f"平台地址: {self.platform_address}")
        print(f"节点URL: {self.node_url}")
        print(f"索引器URL: {self.indexer_url}")
        print(f"轮询间隔: {self.poll_interval}秒")
        print(f"竞标策略: {self.bid_price_ratio * 100}%预算")
        print(f"信誉评分: {self.reputation_score}")
        print("----------------------------------")
    
    def save_state(self, last_sequence_number: int):
        """保存最后处理的事件序列号"""
        state = {"last_processed_sequence_number": last_sequence_number}
        try:
            with open(self.state_file, "w") as f:
                json.dump(state, f)
            print(f"    [State] 状态已保存，序列号: {last_sequence_number}")
        except IOError as e:
            print(f"    [State] 错误: 无法写入状态文件 '{self.state_file}': {e}")
    
    def load_state(self) -> int:
        """加载上次处理的事件序列号"""
        if not os.path.exists(self.state_file):
            return 0
        
        try:
            with open(self.state_file, "r") as f:
                state = json.load(f)
                return int(state.get("last_processed_sequence_number", 0))
        except (IOError, json.JSONDecodeError) as e:
            print(f"    [State] 警告: 无法读取状态文件，从头开始。错误: {e}")
            return 0
    
    def query_indexer_for_new_tasks(self, last_processed_seq_num: int) -> List[Dict]:
        """通过Indexer API查询新的任务发布事件"""
        query = """
        query GetNewTaskEvents($platform_address: String!, $event_type: String!, $last_seq_num: bigint!) {
          events(
            where: {
              account_address: { _eq: $platform_address },
              type: { _eq: $event_type },
              sequence_number: { _gt: $last_seq_num }
            },
            order_by: { sequence_number: asc },
            limit: 25
          ) {
            sequence_number
            data
          }
        }
        """
        
        variables = {
            "platform_address": self.platform_address,
            "event_type": self.event_type,
            "last_seq_num": last_processed_seq_num
        }
        
        try:
            response = requests.post(
                self.indexer_url,
                json={"query": query, "variables": variables},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            if "errors" in data:
                print(f"GraphQL查询错误: {data['errors']}")
                return []
            
            events = data.get("data", {}).get("events", [])
            return events
            
        except requests.RequestException as e:
            print(f"索引器查询错误: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return []
    
    async def place_bid(self, task_id: str, bid_price: int, reputation: int) -> bool:
        """提交竞标"""
        print(f"为任务 '{task_id}' 竞标, 价格: {format_amount(bid_price)}, 信誉: {reputation}")
        
        try:
            client, bidder_account = await get_client_and_account(self.service_agent_profile)
            bidder_addr = str(bidder_account.address())
            
            # 构建交易Payload
            task_id_bytes = format_task_id(task_id)
            payload = EntryFunction.natural(
                f"{self.platform_address}::bidding_system",
                "place_bid",
                [],
                [
                    TransactionArgument(AccountAddress.from_str(self.platform_address), Serializer.struct),
                    TransactionArgument(task_id_bytes, Serializer.sequence_serializer(Serializer.u8)),
                    TransactionArgument(bid_price, Serializer.u64),
                    TransactionArgument(reputation, Serializer.u64),
                ],
            )
            
            # 生成并签名交易
            signed_transaction = await client.create_bcs_signed_transaction(
                bidder_account, TransactionPayload(payload)
            )
            
            # 提交交易
            txn_hash = await client.submit_bcs_transaction(signed_transaction)
            print(f"  > 交易提交中... 哈希: {txn_hash}")
            
            # 等待交易确认
            await client.wait_for_transaction(txn_hash)
            tx_info = await client.transaction_by_hash(txn_hash)
            
            print(f"  > ✅ 竞标成功! 交易版本: {tx_info['version']}")
            await client.close()
            return True
            
        except Exception as e:
            print(f"  > ❌ 竞标失败: {e}")
            return False
    
    async def process_task_event(self, event: Dict) -> bool:
        """处理单个任务事件"""
        try:
            current_seq_num = int(event["sequence_number"])
            task_data = event["data"]
            task_id = task_data["task_id"]
            max_budget = int(task_data["max_budget"])
            
            print(f"\n[发现新任务] ID: {task_id}, 预算: {format_amount(max_budget)}, 序列号: {current_seq_num}")
            
            # 计算竞标价格（预算的指定比例）
            bid_price = int(max_budget * self.bid_price_ratio)
            
            # 提交竞标
            success = await self.place_bid(task_id, bid_price, self.reputation_score)
            
            if success:
                # 成功竞标后保存状态
                self.save_state(current_seq_num)
                return True
            else:
                print(f"处理任务 {task_id} 失败，跳过状态更新")
                return False
                
        except Exception as e:
            print(f"处理事件失败: {e}")
            return False
    
    async def monitor_tasks(self):
        """主监控循环"""
        last_seq_num = self.load_state()
        print(f"\n🚀 Service Agent 监控器启动，从序列号 {last_seq_num} 开始监控...")
        print("正在监控新任务", end="")
        
        try:
            while not shutdown_event.is_set():
                try:
                    # 查询新事件
                    events = self.query_indexer_for_new_tasks(last_seq_num)
                    
                    if not events:
                        print(".", end="", flush=True)
                        # 使用 wait_for 来响应停止信号
                        try:
                            await asyncio.wait_for(asyncio.sleep(self.poll_interval), timeout=1.0)
                        except asyncio.TimeoutError:
                            continue
                        continue
                    
                    # 处理每个事件
                    for event in events:
                        # 检查是否需要停止
                        if shutdown_event.is_set():
                            print(f"\n收到停止信号，保存当前状态...")
                            self.save_state(last_seq_num)
                            return
                            
                        success = await self.process_task_event(event)
                        if success:
                            last_seq_num = int(event["sequence_number"])
                        else:
                            # 如果处理失败，不更新序列号，下次重试
                            break
                    
                    # 短暂休息后继续监控
                    try:
                        await asyncio.wait_for(asyncio.sleep(2), timeout=1.0)
                    except asyncio.TimeoutError:
                        continue
                        
                except Exception as e:
                    print(f"\n监控循环发生错误: {e}")
                    print("等待10秒后重试...")
                    try:
                        await asyncio.wait_for(asyncio.sleep(10), timeout=1.0)
                    except asyncio.TimeoutError:
                        continue
                        
        finally:
            # 确保最终状态被保存
            print(f"\n正在保存最终状态...")
            self.save_state(last_seq_num)
            print("监控服务已优雅停止")


async def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    monitor = ServiceAgentMonitor()
    
    try:
        await monitor.monitor_tasks()
    except Exception as e:
        print(f"服务运行失败: {e}")
        sys.exit(1)
    finally:
        print("服务已完全停止")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # 这里不应该到达，因为信号已经被处理
        print("\n程序被中断")
    except Exception as e:
        print(f"程序异常退出: {e}")
        sys.exit(1)