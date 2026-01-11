from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel, Field

# 2.1 Define Base Strategy Interface

class VisualizationOptions(BaseModel):
    """
    Options for customizing the visualization generation.
    """
    complexity: str = Field(
        "balanced", description="Level of detail/complexity (simple, balanced, detailed)"
    )
    max_depth: int = Field(
        4, description="Maximum depth for hierarchical visualizations like mindmaps"
    )
    style: str = Field(
        "default", description="Specific style or theme for the visualization"
    )

class VisualizationResult(BaseModel):
    """
    Standardized output for any visualization strategy.
    """
    type: str = Field(..., description="Type of visualization (e.g., 'flowchart', 'mindmap')")
    content: str = Field(..., description="The generated visualization code (e.g., Mermaid, Markdown)")
    metadata: Dict[str, Any] = Field({}, description="Additional metadata about the visualization")

class VisualizationStrategy(ABC):
    """
    Abstract base class for all visualization strategies.
    Each concrete strategy must implement methods to generate and validate
    its specific type of visualization.
    """
    @abstractmethod
    async def generate(self, question: str, options: VisualizationOptions) -> VisualizationResult:
        """
        Generates visualization content based on a question and specified options.
        """
        pass

    @abstractmethod
    def validate_content(self, content: str) -> bool:
        """
        Validates the generated content for correctness and adherence to format.
        """
        pass
