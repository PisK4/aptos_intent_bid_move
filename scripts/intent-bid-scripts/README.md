# Aptos Bidding System - Python 脚本

这个目录包含了 Aptos Bidding System 的 Python 交互脚本，基于 `bidding_system.move` 智能合约。

## 脚本列表

### 部署脚本
- `deploy_bidding.py` - 编译、部署和初始化 bidding_system 智能合约

### 核心交互脚本
- `publish_task.py` - Personal Agent 发布任务
- `place_bid.py` - Service Agent 提交竞标
- `select_winner.py` - Personal Agent 选择中标者
- `complete_task.py` - Service Agent 完成任务
- `cancel_task.py` - Personal Agent 取消任务

### 查询脚本
- `view_task.py` - 查看任务详细信息
- `view_platform.py` - 查看平台统计信息

### 通用模块
- `common_bidding.py` - 通用工具函数和配置

## 使用方法

### 1. 使用 uv 虚拟环境 (推荐)

```bash
# 进入脚本目录
cd scripts/intent-bid-scripts

# 创建虚拟环境并安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate

# 运行脚本
uv run deploy_bidding.py --help
```

### 2. 使用 pip 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 运行脚本
python deploy_bidding.py --help
```

## 完整使用流程

### 1. 部署智能合约
```bash
uv run deploy_bidding.py --profile [your_profile](intent_bidding_system)
```

### 2. 发布任务
```bash
uv run publish_task.py "task_001" "设计Logo" 50000 86400
```

### 3. 提交竞标
```bash
uv run place_bid.py "task_001" 40000 85 --profile service_agent_1
uv run place_bid.py "task_001" 35000 92 --profile service_agent_2
```

### 4. 选择中标者
```bash
uv run select_winner.py "task_001"
```

### 5. 完成任务
```bash
uv run complete_task.py "task_001" --profile service_agent_2
```

### 6. 查看信息
```bash
uv run view_task.py "task_001"
uv run view_platform.py
```

## 配置说明

脚本使用 Aptos CLI 配置文件 (`~/.aptos/config.yaml`)，默认使用 `task_manager_dev` profile。

可以通过 `--profile` 参数指定不同的配置文件。

## 注意事项

1. 确保已正确配置 Aptos CLI 和账户
2. 账户需要有足够的 APT 用于 Gas 费用和任务资金
3. 在 devnet 上测试后再部署到 mainnet
4. 所有金额单位为 Octas (1 APT = 10^8 Octas)