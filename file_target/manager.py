# -*- coding: utf-8 -*-
"""
文件目标管理器 (File Target Manager)

统一管理文件目录结构、条件判断、路径解析、元数据追踪。
"""

import os
import json
import time
from typing import Dict, Any, Optional, List, Callable, Tuple
from collections import defaultdict

from .structures import StructureTemplate, DirStructure
from .conditions import Condition, build_condition_from_dict
from .config import FileTargetConfig


class FileTarget:
    """单个文件目标"""
    
    def __init__(self, name: str, condition: Condition, path_template: str,
                 action: Optional[Callable] = None, enabled: bool = True):
        self.name = name
        self.condition = condition
        self.path_template = path_template
        self.action = action
        self.enabled = enabled
        self.trigger_history: List[Dict[str, Any]] = []
    
    def check(self, context: Dict[str, Any]) -> bool:
        if not self.enabled:
            return False
        return self.condition.check(context)
    
    def resolve_path(self, variables: Dict[str, Any]) -> str:
        return self.path_template.format(**variables)
    
    def record_trigger(self, context: Dict[str, Any], path: str):
        self.trigger_history.append({
            "timestamp": time.time(),
            "context": dict(context),
            "path": path,
        })


class FileTargetManager:
    """文件目标管理器"""
    
    def __init__(self, config: Optional[FileTargetConfig] = None, 
                 structure_template: Optional[StructureTemplate] = None,
                 root_dir: str = "./results"):
        self.config = config or FileTargetConfig()
        self.root_dir = root_dir
        self.structure = structure_template or DirStructure.standard_training(root=root_dir)
        self.targets: Dict[str, FileTarget] = {}
        self._paths: Optional[Dict[str, str]] = None
        self._metadata: Dict[str, Any] = {
            "created_at": time.time(),
            "targets": {},
        }
        self._init_directories()
    
    def _init_directories(self):
        """根据模板初始化目录"""
        variables = self._build_variables()
        self._paths = self.structure.create_directories(**variables)
    
    def _build_variables(self) -> Dict[str, str]:
        """构建变量表，用于路径模板替换"""
        return {
            "root": self.root_dir,
            "timestamp": time.strftime("%Y%m%d_%H%M%S"),
            "date": time.strftime("%Y%m%d"),
            **(self.config.get("variables", {}) or {}),
        }
    
    def register(self, name: str, condition: Condition, path_template: str,
                 action: Optional[Callable] = None, enabled: bool = True):
        """注册文件目标"""
        self.targets[name] = FileTarget(name, condition, path_template, action, enabled)
        self._metadata["targets"][name] = {
            "registered_at": time.time(),
            "path_template": path_template,
            "enabled": enabled,
        }
    
    def register_from_config(self, target_configs: List[Dict[str, Any]]):
        """批量从配置注册目标"""
        for cfg in target_configs:
            name = cfg["name"]
            cond = build_condition_from_dict(cfg["condition"])
            path_template = cfg["path_template"]
            enabled = cfg.get("enabled", True)
            self.register(name, cond, path_template, enabled=enabled)
    
    def check(self, name: str, **context) -> bool:
        """检查某个目标的条件是否满足"""
        if name not in self.targets:
            raise KeyError(f"Target '{name}' not registered.")
        return self.targets[name].check(context)
    
    def execute(self, name: str, **context) -> Optional[str]:
        """执行目标对应的文件操作"""
        target = self.targets[name]
        if not target.enabled:
            return None
        
        if not target.check(context):
            return None
        
        variables = self._build_variables()
        variables.update(context)
        if self._paths:
            variables.update(self._paths)
        
        resolved_path = target.resolve_path(variables)
        
        parent_dir = os.path.dirname(resolved_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        
        target.record_trigger(context, resolved_path)
        
        if target.action:
            target.action(context, resolved_path)
        
        return resolved_path
    
    def check_and_execute(self, name: str, **context) -> Optional[str]:
        return self.execute(name, **context)
    
    def check_all(self, **context) -> Dict[str, bool]:
        """检查所有目标"""
        return {name: target.check(context) for name, target in self.targets.items()}
    
    def execute_all(self, **context) -> Dict[str, Optional[str]]:
        """检查并执行所有满足条件的目标"""
        return {name: self.execute(name, **context) for name in self.targets.keys()}
    
    def get_path(self, logical_name: str, **variables) -> str:
        return self.structure.get_path(logical_name, **variables)
    
    def get_resolved_paths(self) -> Dict[str, str]:
        return dict(self._paths) if self._paths else {}
    
    def override_structure(self, overrides: Dict[str, Any]):
        """结构微变：动态修改目录结构"""
        self.structure = self.structure.override(overrides)
        self._init_directories()
    
    def save_metadata(self, path: Optional[str] = None):
        """保存元数据到 JSON"""
        if path is None:
            path = os.path.join(self.root_dir, "file_target_metadata.json")
        
        metadata = {
            **self._metadata,
            "targets_history": {
                name: target.trigger_history
                for name, target in self.targets.items()
            },
            "resolved_paths": self._paths,
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
        
        return path
    
    def reset_conditions(self):
        """重置所有条件的内部状态"""
        for target in self.targets.values():
            target.condition.reset()
    
    def enable(self, name: str):
        if name in self.targets:
            self.targets[name].enabled = True
    
    def disable(self, name: str):
        if name in self.targets:
            self.targets[name].enabled = False
    
    def __repr__(self):
        return (f"FileTargetManager(root='{self.root_dir}', "
                f"targets={list(self.targets.keys())}, "
                f"paths={self._paths})")
