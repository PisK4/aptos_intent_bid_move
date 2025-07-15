#!/usr/bin/env python3
"""
Aptos Bidding System - 部署脚本
负责编译、部署和初始化 bidding_system 智能合约
"""

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path
from aptos_sdk.bcs import Serializer
from aptos_sdk.transactions import (
    EntryFunction,
    TransactionPayload,
    TransactionArgument,
)
from common_bidding import get_client_and_account, get_platform_address, get_function_id, DEFAULT_PROFILE


class BiddingDeployer:
    def __init__(self, profile: str = DEFAULT_PROFILE):
        self.profile = profile
        self.project_root = Path(__file__).parent.parent.parent
        
    def run_command(self, cmd: list, cwd: Path = None) -> tuple[int, str, str]:
        """执行命令并返回结果"""
        if cwd is None:
            cwd = self.project_root
            
        print(f"执行命令: {' '.join(cmd)}")
        print(f"工作目录: {cwd}")
        
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        
        return result.returncode, result.stdout, result.stderr
    
    def compile_contract(self) -> bool:
        """编译智能合约"""
        print("=" * 50)
        print("步骤 1: 编译智能合约")
        print("=" * 50)
        
        # 清理之前的构建
        build_path = self.project_root / "build"
        if build_path.exists():
            import shutil
            shutil.rmtree(build_path)
            print("清理旧的构建文件")
        
        # 编译合约
        cmd = ["aptos", "move", "compile", "--save-metadata"]
        returncode, stdout, stderr = self.run_command(cmd)
        
        if returncode != 0:
            print(f"编译失败: {stderr}")
            return False
        
        print("编译成功!")
        print(f"输出: {stdout}")
        return True
    
    def run_tests(self) -> bool:
        """运行单元测试"""
        print("=" * 50)
        print("步骤 2: 运行单元测试")
        print("=" * 50)
        
        cmd = ["aptos", "move", "test"]
        returncode, stdout, stderr = self.run_command(cmd)
        
        if returncode != 0:
            print(f"测试失败: {stderr}")
            return False
        
        print("测试通过!")
        print(f"输出: {stdout}")
        return True
    
    def deploy_contract(self) -> bool:
        """部署智能合约"""
        print("=" * 50)
        print("步骤 3: 部署智能合约")
        print("=" * 50)
        
        platform_addr = get_platform_address(self.profile)
        print(f"部署地址: {platform_addr}")
        print(f"使用配置: {self.profile}")
        
        # 部署合约
        cmd = [
            "aptos", "move", "publish",
            "--profile", self.profile,
            "--named-addresses", f"aptos_task_manager={platform_addr}",
            "--max-gas", "100000",
            "--gas-unit-price", "100",
            "--assume-yes"
        ]
        
        returncode, stdout, stderr = self.run_command(cmd)
        
        # 检查是否包含错误（区分警告和错误）
        if returncode != 0:
            if "error" in stderr.lower() and "warning" not in stderr.lower():
                print(f"部署失败: {stderr}")
                return False
            else:
                print("部署包含警告信息，但可能成功:")
                print(f"输出: {stdout}")
                print(f"警告: {stderr}")
                # 继续检查是否实际部署成功
        else:
            print("部署成功!")
            print(f"输出: {stdout}")
        
        # 验证部署是否实际成功 - 检查模块是否存在
        print("验证部署状态...")
        verify_cmd = ["aptos", "account", "list", "--profile", self.profile, "--query", "modules"]
        verify_returncode, verify_stdout, verify_stderr = self.run_command(verify_cmd)
        
        if verify_returncode == 0:
            import json
            try:
                result = json.loads(verify_stdout)
                modules = result.get("Result", [])
                
                # 检查是否包含 bidding_system 模块
                has_bidding_system = any("bidding_system" in str(module) for module in modules)
                
                if has_bidding_system:
                    print("✓ bidding_system 模块部署成功")
                    return True
                else:
                    print("✗ bidding_system 模块未找到")
                    print(f"已部署模块: {modules}")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"解析模块列表失败: {e}")
                print(f"原始输出: {verify_stdout}")
                return False
        else:
            print(f"验证部署状态失败: {verify_stderr}")
            return False
    
    async def initialize_platform(self) -> bool:
        """初始化竞标平台"""
        print("=" * 50)
        print("步骤 4: 初始化竞标平台")
        print("=" * 50)
        
        try:
            client, account = await get_client_and_account(self.profile)
            platform_addr = str(account.address())
            
            print(f"平台地址: {platform_addr}")
            print(f"初始化 BiddingPlatform 资源...")
            
            # 构建初始化交易
            payload = EntryFunction.natural(
                f"{platform_addr}::bidding_system",
                "initialize",
                [],  # 无类型参数
                []   # 无函数参数
            )
            
            # 生成并签名交易
            signed_transaction = await client.create_bcs_signed_transaction(
                account, TransactionPayload(payload)
            )
            
            # 提交交易
            txn_hash = await client.submit_bcs_transaction(signed_transaction)
            print(f"交易提交中... 哈希: {txn_hash}")
            
            # 等待交易确认
            await client.wait_for_transaction(txn_hash)
            tx_info = await client.transaction_by_hash(txn_hash)
            
            print(f"初始化成功! 交易版本: {tx_info['version']}")
            return True
            
        except Exception as e:
            print(f"初始化失败: {e}")
            return False
        finally:
            await client.close()
    
    async def verify_deployment(self) -> bool:
        """验证部署状态"""
        print("=" * 50)
        print("步骤 5: 验证部署状态")
        print("=" * 50)
        
        try:
            client, account = await get_client_and_account(self.profile)
            platform_addr = str(account.address())
            
            print(f"检查平台地址: {platform_addr}")
            
            # 检查平台资源是否存在
            resource_type = f"{platform_addr}::bidding_system::BiddingPlatform"
            try:
                resources = await client.account_resources(platform_addr)
                platform_resource = None
                
                for resource in resources:
                    if resource['type'] == resource_type:
                        platform_resource = resource
                        break
                
                if platform_resource:
                    print("✓ BiddingPlatform 资源已创建")
                    print(f"  平台统计: {platform_resource['data']}")
                    return True
                else:
                    print("✗ BiddingPlatform 资源未找到")
                    return False
                    
            except Exception as e:
                print(f"✗ 资源检查失败: {e}")
                return False
                
        except Exception as e:
            print(f"验证失败: {e}")
            return False
        finally:
            await client.close()
    
    async def full_deployment(self) -> bool:
        """完整部署流程"""
        print("Aptos Bidding System 部署开始")
        print(f"配置文件: {self.profile}")
        print(f"项目目录: {self.project_root}")
        
        # 步骤1: 编译
        if not self.compile_contract():
            return False
        
        # 步骤2: 测试
        if not self.run_tests():
            return False
        
        # 步骤3: 部署
        if not self.deploy_contract():
            return False
        
        # 步骤4: 初始化
        if not await self.initialize_platform():
            return False
        
        # 步骤5: 验证
        if not await self.verify_deployment():
            return False
        
        print("=" * 50)
        print("部署完成!")
        print("=" * 50)
        print(f"平台地址: {get_platform_address(self.profile)}")
        print("现在可以使用交互脚本进行操作。")
        
        return True


async def main():
    parser = argparse.ArgumentParser(description="Aptos Bidding System 部署工具")
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        help=f"指定 Aptos CLI 配置文件 (默认: {DEFAULT_PROFILE})"
    )
    parser.add_argument(
        "--step",
        choices=["compile", "test", "deploy", "init", "verify", "all"],
        default="all",
        help="指定执行步骤 (默认: all)"
    )
    
    args = parser.parse_args()
    
    deployer = BiddingDeployer(args.profile)
    
    success = False
    
    if args.step == "compile":
        success = deployer.compile_contract()
    elif args.step == "test":
        success = deployer.run_tests()
    elif args.step == "deploy":
        success = deployer.deploy_contract()
    elif args.step == "init":
        success = await deployer.initialize_platform()
    elif args.step == "verify":
        success = await deployer.verify_deployment()
    elif args.step == "all":
        success = await deployer.full_deployment()
    
    if success:
        print("操作成功完成!")
        sys.exit(0)
    else:
        print("操作失败!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())