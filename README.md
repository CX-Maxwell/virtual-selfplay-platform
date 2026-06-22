# 虚拟自博弈实现平台

> 模块化文件目标系统 + 防空反导自博弈训练平台

## 项目概述

本项目为**防空反导多智能体虚拟自博弈**项目提供模块化的文件目标管理能力。核心设计目标：

- **结构可微调**：目录结构通过模板描述，支持局部 override（微变）
- **条件可修改**：保存、评估、绘图等触发条件通过配置或代码动态定义
- **渐进式复杂**：从最简单的固定间隔，到组合条件、阈值判断、自定义回调，逐步叠加模块

## 快速开始

```python
from platform import SelfPlayPlatform

# 创建平台
platform = SelfPlayPlatform.from_config("platform_config.json")

# 初始化
platform.initialize()

# 训练
platform.train(n_episodes=2000)

# 评估
platform.evaluate(n_episodes=100)
```

## 项目结构

```
├── file_target/          # 模块化文件目标系统（核心）
│   ├── __init__.py
│   ├── structures.py     # 目录结构模板
│   ├── conditions.py     # 可配置条件系统
│   ├── config.py         # 配置系统
│   ├── manager.py        # 文件目标管理器
│   ├── examples/         # 从简单到复杂的示例
│   └── configs/          # 配置示例
├── platform.py           # 整合平台（SelfPlayPlatform）
├── platform_config.json  # 平台配置示例
├── platform_demo.py      # 平台演示
└── USER_MANUAL.md        # 极为详细的使用说明书
```

## 渐进式学习路径

| 阶段 | 难度 | 文件 | 说明 |
|------|------|------|------|
| **Level 1** | 入门 | `simple_example.py` | 固定间隔保存 |
| **Level 2** | 基础 | `intermediate_example.py` | 组合条件 + 结构微变 |
| **Level 3** | 进阶 | `advanced_example.py` | 配置驱动 + 回调 |
| **Level 4** | 熟练 | `platform_demo.py` | 使用统一平台 |

## 核心特性

### 1. 条件系统（由简单到复杂）

```python
from file_target import *

# 简单：固定间隔
c1 = IntervalCondition(500, "episode")

# 中等：阈值触发
c2 = ThresholdCondition("red_win_rate", 0.7, "above")

# 复杂：组合条件
c3 = AndCondition(c1, c2)  # 间隔 AND 阈值
c4 = OrCondition(c1, c2)   # 间隔 OR 阈值
```

### 2. 目录结构模板（可微变）

```python
from file_target import DirStructure

# 使用标准模板
structure = DirStructure.standard_training(root="./results")

# 微变：修改 plots 为 visualizations
new_structure = structure.override({"plots": "visualizations"})
```

### 3. 配置驱动

```json
{
  "targets": [
    {
      "name": "save",
      "condition": {"type": "interval", "interval": 1000, "mode": "episode"},
      "path_template": "{models}/checkpoint_{episode}.pt",
      "enabled": true
    }
  ]
}
```

## 详细文档

请参阅 [USER_MANUAL.md](USER_MANUAL.md) 获取极为详细的使用说明。

## 许可证

MIT License
