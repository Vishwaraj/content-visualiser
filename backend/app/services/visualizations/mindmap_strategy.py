import re
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ValidationError
from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)
from .visualization_strategy import VisualizationStrategy, VisualizationOptions, VisualizationResult
from ..prompt_templates import PromptTemplates

# Create Google Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

class MindmapNode(BaseModel):
    title: str
    children: Optional[List['MindmapNode']] = None

MindmapNode.model_rebuild() # Needed for forward references 

class MindmapStrategy(VisualizationStrategy):
    """
    Strategy for generating and validating mindmap visualizations.
    """
    async def generate(self, question: str, options: VisualizationOptions) -> VisualizationResult:
        """
        Generates mindmap markdown content from a question using the Gemini LLM.
        """
        try:
            logger.info(f"[MINDMAP] Starting generation for question: '{question[:100]}...'")
            prompt = self._build_prompt(question, options)
            logger.debug(f"[MINDMAP] Built prompt with complexity: {options.complexity}, max_depth: {options.max_depth}")
            
            logger.info(f"[MINDMAP] Calling Gemini API (model: {settings.GEMINI_MODEL})...")
            response = await client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,  # A bit creative for mindmaps
                ),
            )
            logger.info(f"[MINDMAP] Received response from Gemini API (length: {len(response.text)} chars)")
            llm_output = response.text
            logger.debug(f"[MINDMAP] Raw LLM output preview: {llm_output[:200]}...")

            # Production-grade error handling: Extract JSON using regex
            json_match = re.search(r'```json\s*(.*?)\s*```', llm_output, re.DOTALL)
            if not json_match:
                raise ValueError("LLM response did not contain a valid JSON block.")

            json_str = json_match.group(1).strip()
            
            json_data = json.loads(json_str)
            mindmap_data = MindmapNode.model_validate(json_data)

            markdown_content = self._json_to_markdown(mindmap_data, options.max_depth)
            logger.info(f"[MINDMAP] Generated markdown content (length: {len(markdown_content)} chars)")

            if not self.validate_content(markdown_content):
                logger.error("[MINDMAP] Validation failed for generated markdown content")
                raise ValueError("Generated mindmap markdown content is invalid.")

            # Calculate metadata
            total_nodes = self._count_nodes(mindmap_data)
            actual_depth = self._calculate_depth(mindmap_data)
            logger.info(f"[MINDMAP] Successfully generated mindmap with {total_nodes} nodes and depth {actual_depth}")

            return VisualizationResult(
                type="mindmap",
                content=markdown_content,
                metadata={
                    "total_nodes": total_nodes,
                    "actual_depth": actual_depth,
                    "requested_max_depth": options.max_depth,
                },
            )
        except ValidationError as e:
            logger.error(f"[MINDMAP] JSON validation failed: {e}")
            raise ValueError(f"LLM generated invalid JSON for Mindmap: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"[MINDMAP] JSON parsing failed: {e}")
            raise ValueError(f"Failed to parse JSON from LLM response: {e}") from e
        except Exception as e:
            # Catch all other exceptions for robust error handling
            logger.exception(f"[MINDMAP] Unexpected error during generation: {e}")
            raise RuntimeError(f"Mindmap generation failed: {e}") from e

    def _detect_domain(self, question: str) -> str:
        """
        Detects the domain of the question to select an appropriate prompt template.
        """
        q_lower = question.lower()
        if any(keyword in q_lower for keyword in ["compare", "vs", "versus", "difference"]):
            return "comparison"
        elif any(keyword in q_lower for keyword in ["learn", "explain", "understand", "teach"]):
            return "learning"
        elif any(keyword in q_lower for keyword in ["process", "workflow", "procedure", "steps"]):
            return "business"
        elif any(keyword in q_lower for keyword in ["how does", "technical", "system", "architecture"]):
            return "technical"
        return "general"


    def _build_prompt(self, question: str, options: VisualizationOptions) -> str:
        """
        Constructs the prompt for the Gemini LLM to generate a mindmap.
        Uses domain detection and complexity guidance.
        """
        domain = self._detect_domain(question)
        base_template = PromptTemplates.get_template(domain)
        complexity_guidance = PromptTemplates.get_complexity_guidance(options.complexity)

        prompt = base_template.format(
            question=question,
            max_depth=options.max_depth,
            complexity_guidance=complexity_guidance,
            json_schema=PromptTemplates.JSON_SCHEMA
        )
        return prompt

    def _json_to_markdown(self, node: MindmapNode, max_depth: int, current_depth: int = 0) -> str:
        """
        Recursively converts the MindmapNode structure into Markdown format.
        """
        if current_depth >= max_depth:
            return ""

        markdown_lines = []
        heading_prefix = "#" * (current_depth + 1)
        markdown_lines.append(f"{heading_prefix} {node.title}")

        if node.children:
            for child in node.children:
                child_markdown = self._json_to_markdown(child, max_depth, current_depth + 1)
                if child_markdown:
                    markdown_lines.append(child_markdown)
        
        return "\n".join(markdown_lines)

    def validate_content(self, content: str) -> bool:
        """
        Validates the generated markdown content for basic structure.
        """
        if not content or len(content.strip()) < 10:
            return False
        
        # Check for at least one markdown heading
        if not re.search(r'^\s*#+\s.+', content, re.MULTILINE):
            return False
        
        # Check length bounds
        if len(content) > 50000: # Markmap might struggle with extremely large inputs
            return False
        
        return True

    def _count_nodes(self, node: MindmapNode) -> int:
        """Recursively counts the total number of nodes in the mindmap."""
        count = 1 # Count self
        if node.children:
            for child in node.children:
                count += self._count_nodes(child)
        return count

    def _calculate_depth(self, node: MindmapNode, current_depth: int = 1) -> int:
        """Recursively calculates the maximum depth of the mindmap."""
        if not node.children:
            return current_depth
        
        max_child_depth = 0
        for child in node.children:
            max_child_depth = max(max_child_depth, self._calculate_depth(child, current_depth + 1))
        
        return max_child_depth
