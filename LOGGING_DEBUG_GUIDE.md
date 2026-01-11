# Logging Improvements - Debug Guide

## Changes Made

Added comprehensive logging throughout the backend to track Gemini API calls and job lifecycle.

## New Log Patterns

### Job Lifecycle Logs
```
[JOB {job_id}] Starting background task for visualization type: {type}
[JOB {job_id}] Attempt {n}/{max}
[JOB {job_id}] Calling generate_visualization...
[JOB {job_id}] Visualization generated successfully!
[JOB {job_id}] Job completed successfully
[JOB {job_id}] Returning final status: {status}
```

### Flowchart Generation Logs
```
[FLOWCHART] Starting generation for question: '{question}'...
[FLOWCHART] Calling Gemini API (model: gemini-2.5-flash)...
[FLOWCHART] Received response from Gemini API (length: X chars)
[FLOWCHART] Generated Mermaid code (length: X chars)
[FLOWCHART] Successfully generated and validated flowchart
```

### Mindmap Generation Logs
```
[MINDMAP] Starting generation for question: '{question}'...
[MINDMAP] Calling Gemini API (model: gemini-2.5-flash)...
[MINDMAP] Received response from Gemini API (length: X chars)
[MINDMAP] Generated markdown content (length: X chars)
[MINDMAP] Successfully generated mindmap with X nodes and depth Y
```

### Error Logs
```
[JOB {job_id}] Gemini ServerError (attempt=X/3, status_code=XXX): {error}
[JOB {job_id}] Retrying after X.Xs due to status XXX
[FLOWCHART] JSON parsing failed: {error}
[MINDMAP] Validation failed for generated markdown content
```

## What to Look For

### 1. **Slow API Response**
Look for time gaps between these log lines:
```
[FLOWCHART] Calling Gemini API...
[FLOWCHART] Received response from Gemini API...
```

If there's a long delay (>30 seconds), the Gemini API is slow or timing out.

### 2. **API Errors**
Look for:
```
[JOB {job_id}] Gemini ServerError
```

Common status codes:
- **429**: Rate limiting (too many requests)
- **503**: Service unavailable (Gemini overloaded)
- **500**: Internal server error

### 3. **Parsing Errors**
Look for:
```
[FLOWCHART] JSON parsing failed
[MINDMAP] JSON validation failed
```

This means Gemini returned invalid JSON format.

### 4. **Validation Errors**
Look for:
```
[FLOWCHART] Validation failed for generated Mermaid code
[MINDMAP] Validation failed for generated markdown content
```

This means the generated content doesn't meet expected structure.

## Debugging Commands

### View real-time logs
```bash
docker-compose logs -f backend
```

### Filter for specific job
```bash
docker-compose logs backend | grep "JOB <job_id>"
```

### Filter for API calls
```bash
docker-compose logs backend | grep "Calling Gemini API"
```

### Filter for errors
```bash
docker-compose logs backend | grep -E "ERROR|FAILED|Exception"
```

## Understanding the Polling Issue

The IP `142.251.222.106` is a Google IP, which is suspicious. This could mean:

1. **Proxy/Load Balancer**: Your requests might be going through a Google Cloud proxy
2. **Docker Network**: The IP might be from Docker's network forwarding
3. **External Service**: Something external is polling your API

The repeated GET requests to `/visualize/{job_id}` are expected - the frontend polls this endpoint every few seconds waiting for the job to complete. This is normal behavior.

## What's Taking So Long?

Based on the logs, check for:

1. **No job start logs** - Background task isn't starting
2. **Long gap between "Calling Gemini" and "Received response"** - API is slow
3. **Retry logs** - API errors causing retries (adds 1.5s, 3s, 6s delays)
4. **Error logs** - Job failed and frontend keeps polling

## Next Steps

After rebuilding with these changes:

```bash
docker-compose build
docker-compose up
```

1. Submit a visualization request
2. Note the job_id from the response
3. Watch logs: `docker-compose logs -f backend | grep "JOB <job_id>"`
4. Look for the patterns above to identify bottlenecks

## Common Issues & Solutions

### Issue: No logs appear after job creation
**Solution**: Background task isn't starting. Check asyncio.create_task() call.

### Issue: "Calling Gemini API" but no response
**Solution**: API timeout or network issue. Check API key and connectivity.

### Issue: Many retry logs
**Solution**: Gemini API is rate-limiting or overloaded. Add delays between requests.

### Issue: JSON parsing errors
**Solution**: Gemini response format changed. Check prompt templates.
