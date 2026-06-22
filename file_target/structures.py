# -*- coding: utf-8 -*-
"""
可配置目录结构模板 (Structure Template)

支持：
- 变量占位符：{name}, {timestamp}, {episode}, {algorithm} 等
- 结构微变（override）：允许对模板局部覆盖
- 嵌套目录树：dict 嵌套描述层级
- 自动创建：运行时一次性 mkdir
"""

import os
import time
from typing import Dict, Any, Optional, List, Union
from copy import deepcopy


class StructureTemplate:
    """目录结构模板
    
    用嵌套 dict 描述目录结构，叶子节点为文件占位符或空目录标记。
    支持变量替换，允许运行时局部 override（结构微变）。
    """
    
    def __init__(self, tree: Dict[str, Any], root: str = "."):
        self.tree = tree
        self.root = root
        self._resolved_cache: Optional[Dict[str, str]] = None
    
    def resolve(self, **variables) -> Dict[str, str]:
        """解析模板，替换变量，返回扁平化的路径映射"""
        result = {}
        self._resolve_recursive(self.tree, self.root, result, variables)
        self._resolved_cache = result
        return result
    
    def _resolve_recursive(self, node: Dict[str, Any], current_path: str, 
                           result: Dict[str, str], variables: Dict[str, str]):
        for key, value in node.items():
            if isinstance(value, dict):
                # 继续嵌套
                sub_dir = os.path.join(current_path, key)
                result[key] = sub_dir  # 记录中间层级路径
                self._resolve_recursive(value, sub_dir, result, variables)
            elif isinstance(value, str):
                # 目录名模板或文件占位符
                resolved_name = value.format(**variables)
                full_path = os.path.join(current_path, resolved_name)
                result[key] = full_path
            elif value is None:
                # 空目录：key 本身作为目录名
                full_path = os.path.join(current_path, key)
                result[key] = full_path
            else:
                raise ValueError(f"Unsupported template value type: {type(value)} for key '{key}'")
    
    def override(self, overrides: Dict[str, Any]) -> "StructureTemplate":
        """结构微变：返回一个新的模板，局部覆盖指定节点"""
        new_tree = deepcopy(self.tree)
        
        def apply_override(tree: Dict, key: str, new_value: Any):
            if key in tree:
                tree[key] = new_value
                return True
            for k, v in tree.items():
                if isinstance(v, dict):
                    if apply_override(v, key, new_value):
                        return True
            return False
        
        for key, new_value in overrides.items():
            if not apply_override(new_tree, key, new_value):
                raise KeyError(f"Override key '{key}' not found in template")
        
        return StructureTemplate(new_tree, root=self.root)
    
    def create_directories(self, **variables) -> Dict[str, str]:
        """解析模板并创建所有目录"""
        paths = self.resolve(**variables)
        for logical_name, path in paths.items():
            os.makedirs(path, exist_ok=True)
        return paths
    
    def get_path(self, logical_name: str, **variables) -> str:
        """获取某个逻辑名对应的解析后路径"""
        paths = self.resolve(**variables)
        if logical_name not in paths:
            raise KeyError(f"Logical name '{logical_name}' not found in template.")
        return paths[logical_name]


class DirStructure:
    """预定义的常用目录结构（可直接选用或作为基线微变）"""
    
    @staticmethod
    def standard_training(root: str = ".") -> StructureTemplate:
        """标准训练结构"""
        return StructureTemplate({
            "root": root,
            "models": {
                "checkpoints": "checkpoints",
                "final": "final",
            },
            "plots": "plots",
            "logs": "logs",
            "data": {
                "replays": "replays",
                "statistics": "statistics",
            },
            "config": "config",
        }, root=root)
    
    @staticmethod
    def experiment_style(root: str = ".", experiment_name: str = "exp_{timestamp}") -> StructureTemplate:
        """实验风格：每个实验独立目录"""
        return StructureTemplate({
            "experiments": {
                "current": experiment_name,
            }
        }, root=root)
    
    @staticmethod
    def hierarchical_style(root: str = ".") -> StructureTemplate:
        """分层风格：按算法/日期/版本分层"""
        return StructureTemplate({
            "runs": {
                "{algorithm}": {
                    "{timestamp}": {
                        "models": "models",
                        "plots": "plots",
                        "logs": "logs",
                    }
                }
            }
        }, root=root)


def build_structure(template_dict: Dict[str, Any], root: str = ".", overrides: Optional[Dict[str, Any]] = None) -> StructureTemplate:
    """便捷函数：从 dict 创建模板，可选应用微变"""
    tmpl = StructureTemplate(template_dict, root=root)
    if overrides:
        tmpl = tmpl.override(overrides)
    return tmpl
