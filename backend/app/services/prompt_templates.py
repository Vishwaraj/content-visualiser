from typing import Dict

class PromptTemplates:
    """
    Manages domain-specific prompt templates for generating mindmaps.
    """

    JSON_SCHEMA = """
Your output MUST be a valid JSON object that adheres to the following schema:
```json
{
  "title": "The central topic of the mindmap",
  "children": [
    {
      "title": "A sub-topic or main branch",
      "children": [
        {
          "title": "A nested sub-topic",
          "children": []
        }
      ]
    }
  ]
}
```
- The root object must have a "title" and a "children" property.
- Each node in the "children" array must also have a "title" and a "children" property.
- The "children" property is an array of nodes, which can be empty.
"""

    TECHNICAL_CONCEPT = """
You are an expert at explaining complex technical concepts as a mindmap.
Topic: {question}

{json_schema}

Suggested main branches for a technical concept:
- Definition
- Key Components
- How It Works
- Use Cases
- Advantages/Disadvantages
- Related Concepts

Maximum depth: {max_depth} levels.
{complexity_guidance}

Return ONLY a valid JSON object, wrapped in ```json ... ``` markdown block.
Do NOT include any other text or explanation outside the JSON block.
"""

    BUSINESS_PROCESS = """
You are an expert at outlining business processes as a mindmap.
Topic: {question}

{json_schema}

Suggested main branches for a business process:
- Overview
- Stakeholders
- Process Steps (sequential flow)
- Inputs/Outputs
- Success Metrics
- Potential Challenges

Maximum depth: {max_depth} levels.
{complexity_guidance}

Return ONLY a valid JSON object, wrapped in ```json ... ``` markdown block.
Do NOT include any other text or explanation outside the JSON block.
"""

    LEARNING_TOPIC = """
You are an expert educator, creating mindmaps for effective learning.
Topic: {question}

{json_schema}

Suggested main branches for a learning topic:
- Core Concepts
- Key Terminology
- Relationships & Connections
- Practical Applications
- Common Misconceptions
- Further Reading/Resources

Maximum depth: {max_depth} levels.
{complexity_guidance}

Return ONLY a valid JSON object, wrapped in ```json ... ``` markdown block.
Do NOT include any other text or explanation outside the JSON block.
"""

    COMPARISON = """
You are an expert at structured comparison, presenting differences and similarities as a mindmap.
Topic: {question} (focus on comparing X and Y)

{json_schema}

Suggested main branches for a comparison:
- Overview of X and Y
- Key Similarities
- Key Differences (e.g., based on features, use cases, performance, cost)
- Pros and Cons of X
- Pros and Cons of Y
- Recommendation/Conclusion

Maximum depth: {max_depth} levels.
{complexity_guidance}

Return ONLY a valid JSON object, wrapped in ```json ... ``` markdown block.
Do NOT include any other text or explanation outside the JSON block.
"""

    _templates: Dict[str, str] = {
        "technical": TECHNICAL_CONCEPT,
        "business": BUSINESS_PROCESS,
        "learning": LEARNING_TOPIC,
        "comparison": COMPARISON,
        "general": TECHNICAL_CONCEPT, # Default fallback
    }

    @classmethod
    def get_template(cls, domain: str) -> str:
        """
        Returns the appropriate prompt template for the given domain.
        Defaults to 'general' (TECHNICAL_CONCEPT) if the domain is not found.
        """
        return cls._templates.get(domain.lower(), cls.TECHNICAL_CONCEPT)

    @classmethod
    def get_complexity_guidance(cls, complexity: str) -> str:
        """
        Returns a string of guidance based on the requested complexity level.
        """
        return {
            "simple": "Keep it high-level: 2-3 main branches, maximum 2 levels deep, 2-5 words per label.",
            "balanced": "Provide a balanced view: 3-5 main branches, moderate detail, 3-4 levels deep, 3-7 words per label.",
            "detailed": "Be comprehensive: 4-6 main branches, detailed explanations with examples, 5-6 levels deep, 4-10 words per label.",
        }.get(complexity.lower(), "Provide a balanced view with good detail.")
