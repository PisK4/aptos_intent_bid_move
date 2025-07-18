# A2A-Aptos MVP Bidding System

一个基于Aptos区块链的去中心化任务竞标系统，实现Personal Agent发布任务和Service Agent自动竞标的完整流程。

## 项目结构

```
bidding_system/
├── README.md                   # 项目说明
├── requirements.txt           # Python依赖
├── pyproject.toml            # 项目配置
├── .env.example              # 环境变量模板
├── common_bidding.py         # 通用工具模块
├── personal_agent_cli.py     # Personal Agent CLI工具
├── service_agent_monitor.py  # Service Agent监控服务
├── deploy_system.py          # 部署和初始化脚本
└── monitor_state.json        # 监控状态文件（运行时生成）
```

## 功能特性

### Personal Agent (任务发布方)
- 发布任务并托管资金
- 选择最优竞标者
- 查询任务状态和竞标详情
- 完成任务结算

### Service Agent (服务提供方)
- 自动监控链上新任务
- 基于策略自动竞标
- 状态持久化，支持重启恢复
- 多任务并发处理

### 系统特性
- 基于Aptos Move智能合约
- 支持多Service Agent竞标
- 价格+声誉+时间的最优匹配算法
- 资金托管和自动结算
- 完整的事件追踪

## 快速开始

### 1. 环境准备

```bash
# 进入项目目录
cd bidding_system

# 安装依赖（推荐使用uv）
uv sync
# 或使用pip
pip install -r requirements.txt

# 复制环境变量模板
cp .env.example .env
```

### 2. 配置Aptos账户

```bash
# 创建部署者账户
aptos init --profile task_manager_dev --network devnet

# 创建Personal Agent账户
aptos init --profile personal_agent --network devnet

# 创建Service Agent账户
aptos init --profile service_agent --network devnet

# 为所有账户申请测试币
aptos account fund-with-faucet --profile task_manager_dev
aptos account fund-with-faucet --profile personal_agent
aptos account fund-with-faucet --profile service_agent
```

### 3. 部署智能合约

```bash
# 在项目根目录编译合约
cd ..
aptos move compile

# 部署合约
aptos move publish --profile task_manager_dev

# 初始化平台
cd bidding_system
python deploy_system.py --initialize-only --profile task_manager_dev
```

### 4. 配置环境变量

编辑 `.env` 文件，填入实际的平台地址：

```env
# 从部署输出中获取平台地址
PLATFORM_ADDRESS=0x你的平台地址

# 配置文件名称
PERSONAL_AGENT_PROFILE=personal_agent
SERVICE_AGENT_PROFILE=service_agent

# 其他配置使用默认值即可
```

## 使用说明

### Personal Agent CLI

```bash
# 发布任务
python personal_agent_cli.py publish "设计公司Logo" --budget 50000000 --deadline 3600

# 查询任务状态
python personal_agent_cli.py status task-12345678

# 选择中标者
python personal_agent_cli.py select-winner task-12345678

# 完成任务
python personal_agent_cli.py complete task-12345678
```

### Service Agent 监控服务

```bash
# 启动监控服务
python service_agent_monitor.py
```

监控服务会：
- 自动发现新发布的任务
- 根据预设策略（默认80%预算）进行竞标
- 保存处理状态，支持重启恢复

## 端到端演示

### 第1步：启动Service Agent监控
```bash
# 终端1
python service_agent_monitor.py
```

### 第2步：发布任务
```bash
# 终端2
python personal_agent_cli.py publish "开发网站" --budget 100000000
```

### 第3步：查看自动竞标
监控服务会自动发现任务并提交竞标。

### 第4步：选择中标者
```bash
python personal_agent_cli.py select-winner task-xxxxxxxx
```

### 第5步：完成任务
```bash
python personal_agent_cli.py complete task-xxxxxxxx
```

## 配置说明

### 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| PLATFORM_ADDRESS | 平台合约地址 | 必须设置 |
| PERSONAL_AGENT_PROFILE | Personal Agent配置文件名 | personal_agent |
| SERVICE_AGENT_PROFILE | Service Agent配置文件名 | service_agent |
| MONITOR_POLL_INTERVAL | 监控轮询间隔（秒） | 5 |
| BID_PRICE_RATIO | 竞标价格比例 | 0.8 |
| SERVICE_AGENT_REPUTATION | Service Agent信誉评分 | 90 |

### 竞标策略

Service Agent使用以下策略进行自动竞标：
- **价格策略**：出价为任务最高预算的80%
- **信誉评分**：固定为90分
- **响应时间**：发现任务后立即竞标

## 故障排除

### 常见错误

1. **导入错误**：确保已安装所有依赖
2. **配置文件找不到**：检查Aptos CLI配置是否正确
3. **平台地址错误**：确保.env中的PLATFORM_ADDRESS正确
4. **余额不足**：确保所有账户都有足够的APT

### 日志和调试

- 监控服务会实时输出处理状态
- 交易哈希可用于在Aptos Explorer中查看详情
- 状态文件`monitor_state.json`记录了处理进度

## 技术架构

### 智能合约层
- `bidding_system.move`：核心竞标逻辑
- 资金托管和自动结算
- 事件驱动的状态更新

### 应用层
- **Personal Agent CLI**：用户交互界面
- **Service Agent Monitor**：自动化竞标服务
- **Common Module**：共享工具和配置

### 数据流
1. Personal Agent发布任务 → 触发TaskPublishedEvent
2. Service Agent监控服务发现事件 → 自动竞标
3. Personal Agent选择中标者 → 任务状态更新
4. Service Agent完成任务 → 资金结算

## 开发和扩展

### 添加新功能
1. 修改智能合约
2. 更新Python SDK调用
3. 测试端到端流程

### 自定义竞标策略
修改`service_agent_monitor.py`中的竞标逻辑：
- 价格计算策略
- 任务筛选条件
- 响应时间优化

## 许可证

本项目采用MIT许可证。