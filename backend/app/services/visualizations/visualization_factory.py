from typing import Dict, Type, List

from .visualization_strategy import VisualizationStrategy
from .flowchart_strategy import FlowchartStrategy
from .mindmap_strategy import MindmapStrategy

class VisualizationFactory:
    """
    Factory for creating instances of VisualizationStrategy based on type.
    """
    _strategies: Dict[str, Type[VisualizationStrategy]] = {}

    def __init__(self):
        # Register strategies upon factory initialization
        self.register_strategy("flowchart", FlowchartStrategy)
        self.register_strategy("mindmap", MindmapStrategy)

    def register_strategy(self, type_name: str, strategy_class: Type[VisualizationStrategy]):
        """
        Registers a new visualization strategy with the factory.
        """
        self._strategies[type_name.lower()] = strategy_class

    def create_strategy(self, type_name: str) -> VisualizationStrategy:
        """
        Creates and returns an instance of the specified visualization strategy.
        Raises ValueError if the type is not supported.
        """
        strategy_class = self._strategies.get(type_name.lower())
        if not strategy_class:
            supported_types = ", ".join(self._strategies.keys())
            raise ValueError(
                f"Unsupported visualization type: '{type_name}'. "
                f"Supported types are: {supported_types}."
            )
        return strategy_class()

    def get_supported_types(self) -> List[str]:
        """
        Returns a list of all supported visualization types.
        """
        return list(self._strategies.keys())

# Create a singleton instance of the factory
visualization_factory = VisualizationFactory()
