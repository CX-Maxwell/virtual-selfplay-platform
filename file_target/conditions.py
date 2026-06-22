# -*- coding: utf-8 -*-
"""
可配置条件系统 (Condition System)

所有条件均继承 Condition 基类，支持：
- 基本触发：Interval, Threshold, Once, Always, Never
- 组合逻辑：And, Or, Not
- 运行时状态：条件可携带内部状态（如计数器、历史记录）
- 配置化构造：从 dict 反序列化

设计目标：
- 条件可改：修改配置即可改变行为，无需改代码
- 条件可组合：复杂逻辑由简单逻辑组合而成
- 条件可追踪：每个条件判断可记录日志
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
import time


class Condition(ABC):
    """条件基类
    
    所有具体条件继承此类，实现 check 方法。
    条件可以是无状态的（如 Threshold），也可以是有状态的（如 Interval）。
    """
    
    name: str = "base"
    
    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._last_result: Optional[bool] = None
        self._last_context: Optional[Dict[str, Any]] = None
    
    @abstractmethod
    def check(self, context: Dict[str, Any]) -> bool:
        """判断条件是否满足
        
        Args:
            context: 运行时上下文，包含 episode, step, reward, metrics 等
        
        Returns:
            True 表示条件满足（触发动作）
        """
        pass
    
    def reset(self):
        """重置条件内部状态（如有）"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为 dict，用于配置保存"""
        return {"type": self.name, **self._kwargs}
    
    def __and__(self, other: "Condition") -> "AndCondition":
        return AndCondition(self, other)
    
    def __or__(self, other: "Condition") -> "OrCondition":
        return OrCondition(self, other)
    
    def __invert__(self) -> "NotCondition":
        return NotCondition(self)
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self._kwargs})"


class IntervalCondition(Condition):
    """间隔条件：每 N 次触发一次
    
    Example:
        cond = IntervalCondition(interval=500, mode="episode")
        # 每 500 个 episode 触发一次
    """
    
    name = "interval"
    
    def __init__(self, interval: int, mode: str = "episode", offset: int = 0):
        super().__init__(interval=interval, mode=mode, offset=offset)
        self.interval = interval
        self.mode = mode
        self.offset = offset
        self._counter = 0
        self._last_time = time.time()
    
    def check(self, context: Dict[str, Any]) -> bool:
        if self.mode == "episode":
            val = context.get("episode", 0)
            return (val + 1 - self.offset) % self.interval == 0
        elif self.mode == "step":
            val = context.get("step", 0)
            return (val + 1 - self.offset) % self.interval == 0
        elif self.mode == "time":
            now = time.time()
            if now - self._last_time >= self.interval:
                self._last_time = now
                return True
            return False
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
    
    def reset(self):
        self._counter = 0
        self._last_time = time.time()


class ThresholdCondition(Condition):
    """阈值条件：指标超过/低于阈值时触发"""
    
    name = "threshold"
    
    def __init__(self, metric: str, threshold: float, direction: str = "above", 
                 window: int = 1, once: bool = False):
        super().__init__(metric=metric, threshold=threshold, direction=direction, 
                         window=window, once=once)
        self.metric = metric
        self.threshold = threshold
        self.direction = direction
        self.window = window
        self.once = once
        self._history: List[float] = []
        self._triggered = False
    
    def check(self, context: Dict[str, Any]) -> bool:
        if self.once and self._triggered:
            return False
        
        value = context.get(self.metric)
        if value is None:
            return False
        
        self._history.append(float(value))
        if len(self._history) > self.window:
            self._history.pop(0)
        
        avg = sum(self._history) / len(self._history)
        
        if self.direction == "above":
            result = avg > self.threshold
        elif self.direction == "below":
            result = avg < self.threshold
        elif self.direction == "eq":
            result = abs(avg - self.threshold) < 1e-6
        else:
            raise ValueError(f"Unknown direction: {self.direction}")
        
        if result and self.once:
            self._triggered = True
        
        self._last_result = result
        self._last_context = dict(context)
        return result
    
    def reset(self):
        self._history.clear()
        self._triggered = False


class OnceCondition(Condition):
    """仅触发一次条件：在指定 episode/step 触发一次"""
    name = "once"
    
    def __init__(self, at: int, mode: str = "episode"):
        super().__init__(at=at, mode=mode)
        self.at = at
        self.mode = mode
        self._triggered = False
    
    def check(self, context: Dict[str, Any]) -> bool:
        if self._triggered:
            return False
        
        val = context.get(self.mode, 0)
        if val >= self.at:
            self._triggered = True
            return True
        return False
    
    def reset(self):
        self._triggered = False


class AlwaysCondition(Condition):
    """总是满足"""
    name = "always"
    
    def check(self, context: Dict[str, Any]) -> bool:
        return True


class NeverCondition(Condition):
    """永不满足"""
    name = "never"
    
    def check(self, context: Dict[str, Any]) -> bool:
        return False


class AndCondition(Condition):
    """与条件：所有子条件都满足"""
    name = "and"
    
    def __init__(self, *conditions: Condition):
        super().__init__()
        self.conditions = list(conditions)
    
    def check(self, context: Dict[str, Any]) -> bool:
        return all(c.check(context) for c in self.conditions)
    
    def to_dict(self) -> Dict[str, Any]:
        return {"type": "and", "conditions": [c.to_dict() for c in self.conditions]}
    
    def reset(self):
        for c in self.conditions:
            c.reset()


class OrCondition(Condition):
    """或条件：任一子条件满足"""
    name = "or"
    
    def __init__(self, *conditions: Condition):
        super().__init__()
        self.conditions = list(conditions)
    
    def check(self, context: Dict[str, Any]) -> bool:
        return any(c.check(context) for c in self.conditions)
    
    def to_dict(self) -> Dict[str, Any]:
        return {"type": "or", "conditions": [c.to_dict() for c in self.conditions]}
    
    def reset(self):
        for c in self.conditions:
            c.reset()


class NotCondition(Condition):
    """非条件：取反"""
    name = "not"
    
    def __init__(self, condition: Condition):
        super().__init__()
        self.condition = condition
    
    def check(self, context: Dict[str, Any]) -> bool:
        return not self.condition.check(context)
    
    def to_dict(self) -> Dict[str, Any]:
        return {"type": "not", "condition": self.condition.to_dict()}
    
    def reset(self):
        self.condition.reset()


CONDITION_REGISTRY = {
    "interval": IntervalCondition,
    "threshold": ThresholdCondition,
    "once": OnceCondition,
    "always": AlwaysCondition,
    "never": NeverCondition,
    "and": AndCondition,
    "or": OrCondition,
    "not": NotCondition,
}


def build_condition_from_dict(config: Dict[str, Any]) -> Condition:
    """从 dict 配置构造条件"""
    cond_type = config.get("type", "always")
    
    if cond_type in ("and", "or"):
        sub_conditions = [build_condition_from_dict(c) for c in config["conditions"]]
        return CONDITION_REGISTRY[cond_type](*sub_conditions)
    elif cond_type == "not":
        sub = build_condition_from_dict(config["condition"])
        return NotCondition(sub)
    else:
        cls = CONDITION_REGISTRY.get(cond_type, AlwaysCondition)
        kwargs = {k: v for k, v in config.items() if k != "type"}
        return cls(**kwargs)


def register_condition(name: str, cls: type):
    """注册自定义条件类型"""
    CONDITION_REGISTRY[name] = cls
