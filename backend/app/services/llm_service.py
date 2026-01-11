import json
import logging
from typing import List

from google import genai
from google.genai import types, errors

from app.core.config import settings

# Configure logging to show INFO level logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


logger = logging.getLogger(__name__)
from .visualizations.visualization_factory import visualization_factory
from .visualizations.visualization_strategy import VisualizationOptions, VisualizationResult

# Create Google Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)


async def check_gemini_connection():
    """Simple health check to verify API key works."""
    try:
        logger.info("Testing Gemini API connection...")
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents="Reply with only the word 'OK'.",
        )
        logger.info(f"Gemini API connection successful. Response: {response.text.strip()}")
        return response.text.strip()
    except Exception as e:  # pragma: no cover - simple connectivity helper
        logger.error(f"Gemini API connection failed: {str(e)}")
        return f"Error: {str(e)}"


async def list_models():
    """Lists available Gemini models."""
    try:
        models_response = await client.aio.models.list()
        models = [m for m in models_response if hasattr(m, 'supported_generation_methods') 
                  and 'generateContent' in m.supported_generation_methods]
        return models
    except Exception as e:  # pragma: no cover - simple connectivity helper
        return f"Error: {str(e)}"


async def generate_visualization(
    question: str,
    visualization_type: str,
    options: VisualizationOptions,
) -> VisualizationResult:
    """
    Generates a visualization using the appropriate strategy.
    """
    try:
        strategy = visualization_factory.create_strategy(visualization_type)
        result = await strategy.generate(question, options)
        return result
    except ValueError as e:
        # Catch specific strategy-related validation errors or unsupported types
        raise ValueError(f"Visualization error: {e}") from e
    except Exception as e:
        # Catch all other unexpected errors
        raise RuntimeError(f"Failed to generate visualization of type '{visualization_type}': {e}") from e


def get_supported_visualization_types() -> List[str]:
    """
    Returns a list of all supported visualization types from the factory.
    """
    return visualization_factory.get_supported_types()
