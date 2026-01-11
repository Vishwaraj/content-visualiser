import json
import logging
import re
from typing import Dict, Any, List
from pydantic import ValidationError
from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)
from .visualization_strategy import VisualizationStrategy, VisualizationOptions, VisualizationResult
from ..prompt_templates import PromptTemplates

# Create Google Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

class FlowchartStrategy(VisualizationStrategy):
    """
    Strategy for generating and validating flowchart visualizations.
    """
    async def generate(self, question: str, options: VisualizationOptions) -> VisualizationResult:
        """
        Generates Mermaid flowchart code from a question using the Gemini LLM.
        """
        try:
            logger.info(f"[FLOWCHART] Starting generation for question: '{question[:100]}...'")
            prompt = self._build_prompt(question, options)
            logger.debug(f"[FLOWCHART] Built prompt with complexity: {options.complexity}")
            
            logger.info(f"[FLOWCHART] Calling Gemini API (model: {settings.GEMINI_MODEL})...")
            response = await client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.4,  # Less creative for flowcharts
                ),
            )
            logger.info(f"[FLOWCHART] Received response from Gemini API (length: {len(response.text)} chars)")
            raw_llm_output = response.text
            logger.debug(f"[FLOWCHART] Raw LLM output preview: {raw_llm_output[:200]}...")

            # Production-grade error handling: Extract JSON using regex
            # LLM can sometimes add conversational text or markdown around the JSON
            json_match = re.search(r'```json\s*(.*?)\s*```', raw_llm_output, re.DOTALL)
            if not json_match:
                # Fallback: if no markdown json block, try to parse the whole output as JSON
                try:
                    diagram = json.loads(raw_llm_output)
                except json.JSONDecodeError:
                    raise ValueError("LLM response did not contain a valid JSON block or raw JSON.")
            else:
                json_str = json_match.group(1).strip()
                diagram = json.loads(json_str)

            mermaid_code = self._json_to_mermaid(diagram)
            logger.info(f"[FLOWCHART] Generated Mermaid code (length: {len(mermaid_code)} chars)")

            if not self.validate_content(mermaid_code):
                logger.error("[FLOWCHART] Validation failed for generated Mermaid code")
                raise ValueError("Generated Mermaid flowchart content is invalid.")

            logger.info("[FLOWCHART] Successfully generated and validated flowchart")
            # No specific metadata for flowchart yet, but can be extended
            return VisualizationResult(
                type="flowchart",
                content=mermaid_code,
                metadata={},
            )
        except json.JSONDecodeError as e:
            logger.error(f"[FLOWCHART] JSON parsing failed: {e}")
            raise ValueError(f"Failed to parse JSON from LLM response: {e}") from e
        except Exception as e:
            logger.exception(f"[FLOWCHART] Unexpected error during generation: {e}")
            raise RuntimeError(f"Flowchart generation failed: {e}") from e

    def _build_prompt(self, question: str, options: VisualizationOptions) -> str:
        """
        Constructs the prompt for the Gemini LLM to generate a flowchart.
        """
        complexity_guidance = PromptTemplates.get_complexity_guidance(options.complexity)
        
        # Adjust prompt based on options, e.g., complexity could influence the number of nodes/edges
        prompt = f"""
You are an expert technical explainer and diagram designer.
The user is asking: "{question}".

Your task is to design a clear, high-level flow of how this works and represent that flow as a JSON object.
This JSON will then be used to generate a Mermaid flowchart.

JSON schema:
```json
{{
  "type": "flowchart",
  "direction": "TD" | "LR",
  "nodes": [
    {{"id": "A1", "label": "Start Node Label", "shape": "start"}},
    {{"id": "B1", "label": "Process Step", "shape": "process"}},
    {{"id": "C1", "label": "Decision Point", "shape": "decision"}},
    {{"id": "D1", "label": "End Node Label", "shape": "end"}}
  ],
  "edges": [
    {{"from": "A1", "to": "B1", "label": "optional edge label"}}
  ]
}}
```
Supported Node Shapes:
- "start": `([])` (e.g., A(["Start"]))
- "end": `(())` (e.g., Z(End)) - corrected, original was `([])` for both
- "decision": `{{}}` (e.g., C{{"Is it true?"}})
- "inputoutput": `[//]` (e.g., D[//"Input/Output"/])
- "process": `[]` (e.g., B["Process"])
- Default (if shape not specified or unknown): `[]`

Important:
- Respond with valid, parseable JSON only.
- Wrap the JSON in a ```json ... ``` markdown block.
- Do NOT include any text before or after the JSON block.
- Ensure node IDs are unique and alphanumeric.
- {complexity_guidance}
"""
        return prompt

    def _json_to_mermaid(self, diagram: dict) -> str:
        """Convert a simple JSON diagram description into Mermaid flowchart code."""
        direction = diagram.get("direction", "TD")
        nodes = diagram.get("nodes", [])
        edges = diagram.get("edges", [])

        lines: list[str] = [f"flowchart {direction}"]

        node_shapes = {
            "start": ["([", "])"], # Adjusted to match flowchart start/end common shapes
            "end": ["((", "))"],   # Corrected to match flowchart end common shape
            "decision": ["{", "}"],
            "inputoutput": ["[/", "/]"],
            "process": ["[", "]"],
            "default": ["[", "]"],
        }

        for node in nodes:
            node_id = node.get("id", "").strip()
            label = node.get("label", "").strip()
            shape_key = node.get("shape", "default").lower()
            
            if not node_id:
                continue

            safe_id = "".join(ch for ch in node_id if ch.isalnum() or ch == "_") # Allow underscore for node IDs
            if not safe_id:
                continue

            # Escape double quotes in labels for Mermaid
            safe_label = label.replace('"', '&quot;') or safe_id

            open_shape, close_shape = node_shapes.get(shape_key, node_shapes["default"])
            lines.append(f'{safe_id}{open_shape}"{safe_label}"{close_shape}')

        for edge in edges:
            src = edge.get("from", "").strip()
            dst = edge.get("to", "").strip()
            if not src or not dst:
                continue

            safe_src = "".join(ch for ch in src if ch.isalnum() or ch == "_")
            safe_dst = "".join(ch for ch in dst if ch.isalnum() or ch == "_")
            if not safe_src or not safe_dst:
                continue

            label = edge.get("label", "").strip()
            if label:
                safe_label = label.replace('"', '&quot;')
                lines.append(f'{safe_src} -->|"{safe_label}"| {safe_dst}')
            else:
                lines.append(f"{safe_src} --> {safe_dst}")

        # Fallback if nothing was produced
        if len(lines) == 1:
            lines.extend(
                [
                    'A(["Unable to build diagram"])',
                    'A --> B(("Please refine your question"))', # Corrected fallback
                ]
            )

        return "\n".join(lines)

    def validate_content(self, content: str) -> bool:
        """
        Validates the generated Mermaid content for basic correctness.
        Checks for the 'flowchart' keyword.
        """
        if not content or len(content.strip()) < 10:
            return False
        
        # Check for the flowchart declaration at the beginning
        if not content.strip().startswith("flowchart"):
            return False
        
        # Simple check for nodes and edges (optional, as LLM output might be minimal)
        # if not re.search(r'\b\w+\s*(-->|<--)\s*\w+\b', content): # Checks for A --> B pattern
        #     return False
        
        # Check length bounds
        if len(content) > 50000: # Mermaid might struggle with extremely large inputs
            return False
        
        return True
