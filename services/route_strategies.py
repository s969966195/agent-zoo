"""
Route Strategies for Zoo Multi-Agent A2A System.

Defines execution strategies for routing @mentions between animals:
- Serial execution: Sequential order
- Dynamic worklist growth: Adaptive expansion
"""

import asyncio
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from utils.a2a_mentions import ANIMAL_CONFIGS


@dataclass
class RouteTask:
    """A task to route to an animal."""
    animal_key: str
    content: str
    depth: int
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class RouteResult:
    """Result of a routing operation."""
    animal_key: str
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class RouteStrategy(ABC):
    """Abstract base class for route strategies."""
    
    @abstractmethod
    def name(self) -> str:
        """Strategy name."""
        pass
    
    @abstractmethod
    async def execute(
        self,
        tasks: List[RouteTask],
        execute_fn: Callable[[RouteTask], asyncio.Task],
    ) -> List[RouteResult]:
        """
        Execute tasks using this strategy.
        
        Args:
            tasks: List of tasks to execute
            execute_fn: Function that creates an async task for a task
            
        Returns:
            List of results
        """
        pass


class SerialRouteStrategy(RouteStrategy):
    """
    Serial execution strategy.
    
    Routes mentions one at a time in order.
    Simple and predictable, but slower for multiple animals.
    """
    
    def name(self) -> str:
        return "serial"
    
    async def execute(
        self,
        tasks: List[RouteTask],
        execute_fn: Callable[[RouteTask], asyncio.Task],
    ) -> List[RouteResult]:
        """Execute tasks in serial order."""
        results = []
        
        for task in tasks:
            try:
                task_result = await execute_fn(task)
                results.append(task_result)
            except Exception as e:
                results.append(RouteResult(
                    animal_key=task.animal_key,
                    success=False,
                    error=str(e),
                ))
        
        return results


class DynamicWorklistStrategy(RouteStrategy):
    """
    Dynamic worklist growth strategy.
    
    Starts with a small subset of tasks and expands worklist
    as responses come in. Prevents overwhelming animals.
    
    Attributes:
        initial_size: Number of tasks to start with
        growth_factor: Multiplier for worklist expansion
        max_batch_size: Maximum tasks in a batch
    """
    
    def __init__(
        self,
        initial_size: int = 2,
        growth_factor: float = 1.5,
        max_batch_size: int = 10,
    ):
        """
        Initialize dynamic worklist strategy.
        
        Args:
            initial_size: Initial number of tasks
            growth_factor: How much to grow worklist
            max_batch_size: Maximum batch size
        """
        self.initial_size = min(initial_size, 10)  # Safe minimum
        self.growth_factor = growth_factor
        self.max_batch_size = max_batch_size
    
    def name(self) -> str:
        return "dynamic_worklist"
    
    async def execute(
        self,
        tasks: List[RouteTask],
        execute_fn: Callable[[RouteTask], asyncio.Task],
    ) -> List[RouteResult]:
        """Execute tasks with dynamic worklist expansion."""
        if not tasks:
            return []
        
        results = []
        remaining_tasks = tasks.copy()
        completed_animals: Set[str] = set()
        
        # Initial batch
        batch_size = min(self.initial_size, len(remaining_tasks))
        current_batch = remaining_tasks[:batch_size]
        remaining_tasks = remaining_tasks[batch_size:]
        
        while current_batch:
            # Execute current batch concurrently
            batch_tasks = [execute_fn(task) for task in current_batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process batch results
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    results.append(RouteResult(
                        animal_key=current_batch[i].animal_key,
                        success=False,
                        error=str(result),
                    ))
                else:
                    results.append(result)
                    completed_animals.add(current_batch[i].animal_key)
            
            # Dynamic worklist growth
            if remaining_tasks and len(completed_animals) > 0:
                # Calculate new batch size with growth factor
                growth = int(len(completed_animals) * self.growth_factor)
                new_size = min(
                    max(1, growth),
                    self.max_batch_size,
                    len(remaining_tasks),
                )
                
                # Add new tasks to batch
                current_batch = remaining_tasks[:new_size]
                remaining_tasks = remaining_tasks[new_size:]
            else:
                current_batch = []
        
        return results


class AdaptiveStrategy(RouteStrategy):
    """
    Adaptive strategy that chooses between serial and dynamic
    based on workload characteristics.
    
    Uses serial for small workloads (< 3 tasks), dynamic otherwise.
    """
    
    def __init__(
        self,
        dynamic_strategy: Optional[DynamicWorklistStrategy] = None,
    ):
        """Initialize adaptive strategy."""
        self.dynamic_strategy = dynamic_strategy or DynamicWorklistStrategy()
        self._serial = SerialRouteStrategy()
    
    def name(self) -> str:
        return "adaptive"
    
    async def execute(
        self,
        tasks: List[RouteTask],
        execute_fn: Callable[[RouteTask], asyncio.Task],
    ) -> List[RouteResult]:
        """Execute with adaptive strategy selection."""
        if not tasks:
            return []
        
        # Choose strategy based on workload
        if len(tasks) < 3:
            return await self._serial.execute(tasks, execute_fn)
        else:
            return await self.dynamic_strategy.execute(tasks, execute_fn)


def create_strategy(name: str, **kwargs) -> RouteStrategy:
    """
    Factory function to create route strategies.
    
    Args:
        name: Strategy name
        **kwargs: Strategy parameters
        
    Returns:
        Configured route strategy
    """
    strategies = {
        "serial": SerialRouteStrategy,
        "dynamic_worklist": DynamicWorklistStrategy,
        "adaptive": AdaptiveStrategy,
    }
    
    strategy_class = strategies.get(name.lower())
    if not strategy_class:
        raise ValueError(f"Unknown strategy: {name}")
    
    return strategy_class(**kwargs)


# Constants for A2A execution
DEFAULT_DEPTH_LIMIT = 15
DEFAULT_INITIAL_BATCH = 2
DEFAULT_GROWTH_FACTOR = 1.5

# Animal name mapping for routing
ANIMAL_NAME_MAPPING = {
    "雪球": "xueqiu",
    "xueqiu": "xueqiu",
    "六六": "liuliu",
    "liuliu": "liuliu",
    "小黄": "xiaohuang",
    "xiaohuang": "xiaohuang",
}

def normalize_animal_key(animal_key: str) -> str:
    """Normalize animal key to standard format."""
    return ANIMAL_NAME_MAPPING.get(animal_key.lower(), animal_key.lower())


def validate_depth(depth: int, max_depth: int = DEFAULT_DEPTH_LIMIT) -> bool:
    """Validate that depth is within allowed range."""
    return 0 <= depth <= max_depth


def get_next_depth(current_depth: int) -> int:
    """Calculate next depth level."""
    if not validate_depth(current_depth):
        raise ValueError(f"Invalid depth: {current_depth}")
    return current_depth + 1
