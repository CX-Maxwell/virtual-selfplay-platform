# -*- coding: utf-8 -*-
"""
模块化文件目标系统 (Modular File Target System)

功能：
1. 可配置目录结构 —— 通过模板定义文件/目录组织方式，支持变量替换与结构微变
2. 条件可改 —— 保存、评估、记录等触发条件支持动态配置与组合
3. 统一管理 —— 集中处理所有文件路径创建、条件判断、元数据追踪

设计原则：
- 结构模板化：目录树用嵌套 dict 描述，运行时解析为真实路径
- 条件插件化：所有条件继承 Condition 基类，支持 AND/OR/NOT 组合
- 微变安全：结构模板允许局部 override，不影响整体框架
"""

from .config import FileTargetConfig, load_config, merge_config
from .structures import DirStructure, StructureTemplate, build_structure
from .conditions import (
    Condition,
    IntervalCondition,
    ThresholdCondition,
    OnceCondition,
    AlwaysCondition,
    NeverCondition,
    AndCondition,
    OrCondition,
    NotCondition,
    build_condition_from_dict,
)
from .manager import FileTargetManager

__all__ = [
    # 配置
    "FileTargetConfig",
    "load_config",
    "merge_config",
    # 结构
    "DirStructure",
    "StructureTemplate",
    "build_structure",
    # 条件
    "Condition",
    "IntervalCondition",
    "ThresholdCondition",
    "OnceCondition",
    "AlwaysCondition",
    "NeverCondition",
    "AndCondition",
    "OrCondition",
    "NotCondition",
    "build_condition_from_dict",
    # 管理器
    "FileTargetManager",
]
