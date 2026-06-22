# -*- coding: utf-8 -*-
"""
配置文件系统 (Configuration System)

支持 YAML/JSON 配置加载、多配置合并、运行时动态修改。
"""

import os
import json
from typing import Dict, Any, Optional
from copy import deepcopy


class FileTargetConfig:
    """文件目标配置
    
    封装一个 dict 配置，提供便捷访问和合并方法。
    """
    
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self._data = deepcopy(data) if data else {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """点分隔访问嵌套配置，如 'structure.templates'"""
        keys = key.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split(".")
        target = self._data
        for k in keys[:-1]:
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
    
    def merge(self, other: "FileTargetConfig") -> "FileTargetConfig":
        """深度合并另一个配置，返回新实例"""
        merged = deepcopy(self._data)
        
        def _merge(base: Dict, update: Dict):
            for k, v in update.items():
                if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                    _merge(base[k], v)
                else:
                    base[k] = deepcopy(v)
        
        _merge(merged, other._data)
        return FileTargetConfig(merged)
    
    def to_dict(self) -> Dict[str, Any]:
        return deepcopy(self._data)
    
    @classmethod
    def from_yaml(cls, path: str) -> "FileTargetConfig":
        """从 YAML 文件加载"""
        try:
            import yaml
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return cls(data)
        except ImportError:
            raise ImportError("PyYAML is required to load YAML config.")
    
    @classmethod
    def from_json(cls, path: str) -> "FileTargetConfig":
        """从 JSON 文件加载"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data)
    
    def save_yaml(self, path: str):
        """保存为 YAML 文件"""
        try:
            import yaml
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(self._data, f, allow_unicode=True, default_flow_style=False)
        except ImportError:
            raise ImportError("PyYAML is required to save YAML config.")
    
    def save_json(self, path: str):
        """保存为 JSON 文件"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
    
    def __repr__(self):
        return f"FileTargetConfig({json.dumps(self._data, indent=2, ensure_ascii=False)})"


def load_config(path: str) -> FileTargetConfig:
    """根据文件后缀自动加载配置"""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".yaml", ".yml"):
        return FileTargetConfig.from_yaml(path)
    elif ext == ".json":
        return FileTargetConfig.from_json(path)
    else:
        try:
            return FileTargetConfig.from_yaml(path)
        except Exception:
            return FileTargetConfig.from_json(path)


def merge_config(base: FileTargetConfig, override: FileTargetConfig) -> FileTargetConfig:
    """合并两个配置"""
    return base.merge(override)
