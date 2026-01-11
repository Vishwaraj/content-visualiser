# Migration to google-genai Package - Changes Summary

## Issue
Backend was failing with `ModuleNotFoundError: No module named 'google.generativeai'` when running in Docker.

## Root Cause
The code was using the old/legacy `google.generativeai` package imports, but `requirements.txt` had the new `google-genai==1.56.0` package installed.

## Solution
Migrated all code to use the new `google-genai` API (v1.56.0) which is the official, actively maintained SDK.

## Files Modified

### 1. `/backend/app/services/llm_service.py`
**Changes:**
- Changed import from `import google.generativeai as genai` to `from google import genai`
- Changed error import from `from google.generativeai import errors as genai_errors` to `from google.genai import types, errors`
- Replaced `genai.configure(api_key=...)` with `client = genai.Client(api_key=...)`
- Updated `check_gemini_connection()` to use new async client API:
  - Old: `model = genai.GenerativeModel(...); response = await model.generate_content_async(...)`
  - New: `response = await client.aio.models.generate_content(model=..., contents=...)`
- Updated `list_models()` to use new client API:
  - Old: `genai.list_models()`
  - New: `await client.aio.models.list()`

### 2. `/backend/app/services/visualizations/flowchart_strategy.py`
**Changes:**
- Changed import from `import google.generativeai as genai` to `from google import genai`
- Replaced `genai.configure(api_key=...)` with `client = genai.Client(api_key=...)`
- Updated model generation to use new client API:
  - Old: `model = genai.GenerativeModel(..., generation_config=...); response = await model.generate_content_async(...)`
  - New: `response = await client.aio.models.generate_content(model=..., contents=..., config=types.GenerateContentConfig(...))`

### 3. `/backend/app/services/visualizations/mindmap_strategy.py`
**Changes:**
- Changed import from `import google.generativeai as genai` to `from google import genai`
- Replaced `genai.configure(api_key=...)` with `client = genai.Client(api_key=...)`
- Updated model generation to use new client API (same pattern as flowchart_strategy.py)

## Key API Changes

### Old API (google-generativeai)
```python
import google.generativeai as genai

genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel("gemini-2.5-flash")
response = await model.generate_content_async("prompt")
```

### New API (google-genai)
```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")
response = await client.aio.models.generate_content(
    model="gemini-2.5-flash",
    contents="prompt",
    config=types.GenerateContentConfig(temperature=0.7)
)
```

## Testing Steps
1. Rebuild Docker container: `docker-compose build`
2. Start services: `docker-compose up`
3. Verify backend starts without import errors
4. Test API endpoints for mindmap and flowchart generation

## References
- New SDK Documentation: https://googleapis.github.io/python-genai/
- Migration Guide: https://ai.google.dev/gemini-api/docs/libraries
- PyPI Package: https://pypi.org/project/google-genai/
