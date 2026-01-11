# Sprint 1-2: Mindmap MVP Implementation Guide

## Overview

**Goal**: Extend Content Visualizer to support mindmap generation alongside flowcharts using a strategy pattern architecture.

**Duration**: 2 weeks (10 working days)

**Key Deliverables**:
- Mindmap rendering with Markmap library
- Backend strategy pattern for multiple visualization types
- Enhanced UI with type selection
- Fixed configuration issues

---

## Task 1: Add Markmap Library to Frontend (Days 1-2)

### 1.1 Install Dependencies
```bash
npm install markmap-view markmap-lib markmap-toolbar
```

### 1.2 Create Components

**Components to Create**:

1. **`components/visualizations/mindmap-renderer.tsx`**
   - Client component using `useRef` and `useEffect`
   - Import Transformer from markmap-lib to convert markdown to data
   - Import Markmap from markmap-view for rendering
   - Initialize Markmap.create() with SVG ref
   - Add Toolbar.create() for zoom/fit controls
   - Configure options: duration=500ms, maxWidth=300, initialExpandLevel=2
   - Use depth-based color coding
   - Implement cleanup in useEffect return

2. **`components/visualizations/visualization-renderer.tsx`**
   - Unified component that switches between flowchart/mindmap
   - Use dynamic imports with `next/dynamic` for SSR avoidance
   - Check visualization type prop and render appropriate component
   - Add loading state with `useState` and `useEffect` for mounting

### 1.3 Add Styling

**In `app/globals.css`**, add:
- `.markmap` container styles (width: 100%, height: 100%)
- `.markmap-node` cursor and hover effects
- `.markmap-toolbar` positioning (absolute, bottom-right)
- Toolbar button styles with hover states
- Dark mode text and path color overrides
- Minimum height: 500px for mindmap container

---

## Task 2: Create Backend Strategy Pattern (Days 3-5)

### 2.1 Define Base Strategy Interface

**Create `services/visualization_strategy.py`**:
- Define `VisualizationOptions` Pydantic model with: complexity (simple/balanced/detailed), max_depth (default: 4), style
- Define `VisualizationResult` Pydantic model with: type, content, metadata dict
- Create abstract `VisualizationStrategy` class with:
  - Abstract method: `generate(question, options) -> VisualizationResult`
  - Abstract method: `validate_content(content) -> bool`

### 2.2 Implement MindmapStrategy

**Create `services/mindmap_strategy.py`**:

**Core Methods**:
1. `generate()`:
   - Build prompt using `_build_prompt()`
   - Call LLM with async: `model.generate_content_async(prompt)`
   - Extract JSON using regex: `r'```json\s*(.*?)\s*```'`
   - Parse JSON and convert to markdown with `_json_to_markdown()`
   - Validate and return VisualizationResult

2. `_build_prompt()`:
   - Include complexity guidance based on options
   - Specify max_depth limit
   - Define JSON schema with title and nested children
   - Emphasize: "Return ONLY valid JSON, no markdown formatting"
   - Require concise node titles (3-7 words)

3. `_json_to_markdown()`:
   - Recursive function with current_depth parameter
   - Use heading levels: `"#" * (current_depth + 1)`
   - Process children recursively
   - Stop at max_depth

4. `validate_content()`:
   - Check for non-empty content
   - Verify at least one markdown heading exists
   - Check length bounds (10-50000 chars)

5. Helper methods:
   - `_calculate_depth()`: Recursive depth calculation
   - `_count_nodes()`: Total node counter for metadata

### 2.3 Refactor FlowchartStrategy

**Create `services/flowchart_strategy.py`**:
- Move existing flowchart logic from llm_service.py
- Implement same VisualizationStrategy interface
- `generate()` returns VisualizationResult with Mermaid code
- `_json_to_mermaid()` converts JSON nodes/edges to Mermaid syntax
- Node type shapes: start/end = `([])`, decision = `{}`, input/output = `[//]`, process = `[]`
- `validate_content()` checks for "flowchart" prefix

### 2.4 Create Strategy Factory

**Create `services/visualization_factory.py`**:
- Maintain `_strategies` dict mapping types to strategy classes
- `create_strategy(type, model)` returns strategy instance
- Raise ValueError for unsupported types with helpful message
- `get_supported_types()` returns list of available types
- Register: "flowchart" -> FlowchartStrategy, "mindmap" -> MindmapStrategy

### 2.5 Refactor LLM Service

**Update `services/llm_service.py`**:
- Keep Gemini model initialization
- Replace direct generation with factory pattern
- `generate_visualization(question, type, options)`:
  - Create strategy via factory
  - Delegate to strategy.generate()
  - Return VisualizationResult
  - Wrap errors with context
- Add `get_supported_types()` that proxies to factory
- Remove all direct Mermaid/diagram generation code

---

## Task 3: Advanced LLM Prompt Engineering (Days 6-7)

### 3.1 Create Domain-Specific Prompt Templates

**Create `services/prompt_templates.py`**:

**Define Template Categories**:
1. **TECHNICAL_CONCEPT**: Branches = Definition, Components, How It Works, Use Cases, Pros/Cons
2. **BUSINESS_PROCESS**: Branches = Overview, Stakeholders, Process Steps, Tools, Metrics
3. **LEARNING_TOPIC**: Branches = Core Concepts, Terminology, Relationships, Applications, Practice
4. **COMPARISON**: Branches = Overview, Common Features, Differences, Pros/Cons, Recommendations

**Template Structure**:
- Start with role definition: "You are explaining a [domain] as a mindmap"
- Include topic: "Topic: {question}"
- List suggested main branches (4-6)
- Specify max_depth placeholder: "Maximum depth: {max_depth} levels"
- End with: "Return JSON structure"

**Class Methods**:
- `get_template(domain)` returns appropriate template string
- Default to TECHNICAL_CONCEPT if domain unknown

### 3.2 Implement Domain Detection

**Update MindmapStrategy**:

Add `_detect_domain(question)` method:
- Convert question to lowercase
- Keyword matching:
  - "compare", "vs", "versus", "difference" → "comparison"
  - "learn", "explain", "understand", "teach" → "learning"
  - "process", "workflow", "procedure", "steps" → "business"
  - "how does", "technical", "system", "architecture" → "technical"
- Return "general" as fallback

Update `_build_prompt()`:
- Call `_detect_domain(question)`
- If domain != "general", use PromptTemplates.get_template(domain)
- Format template with question and max_depth
- Otherwise use default prompt logic

### 3.3 Complexity-Based Prompt Variations

**Enhance `_build_prompt()`**:

Define complexity guidance dict:
- **simple**: "2-3 main branches, maximum 2 levels, 2-5 words per label"
- **balanced**: "3-5 main branches, moderate detail, standard depth"
- **detailed**: "4-6 main branches, comprehensive with examples, maximum depth"

Inject appropriate guidance into prompt based on `options.complexity`

---

## Task 4: Enhanced UI with Type Selection (Days 8-9)

### 4.1 Create Visualization Type Selector

**Create `components/ui/visualization-type-selector.tsx`**:

**Component Structure**:
- Props: value (VisualizationType), onChange, disabled
- Define type constant: `type VisualizationType = 'flowchart' | 'mindmap'`
- Array of visualization types with metadata:
  - id, name, description, icon (from lucide-react), color classes

**Visual Design**:
- Grid layout: 2 columns on desktop, 1 on mobile
- Each type as a Card component
- Card content: Icon with background color, name, description
- Selected state: ring-2 ring-primary, pulse indicator
- Hover effects: shadow-lg, border-primary/50
- Disabled state: opacity-50, cursor-not-allowed

**Icons**:
- Flowchart: GitBranch (blue theme)
- Mindmap: Network (purple theme)

### 4.2 Update Main Page

**Modify `app/page.tsx`**:

**New State Variables**:
- `visualizationType: VisualizationType` (default: 'flowchart')
- Keep existing: question, jobId, status, diagramCode, loading, error

**UI Flow Changes**:
1. Add VisualizationTypeSelector above textarea
2. Label: "Choose Visualization Type"
3. Pass visualizationType and setter to selector
4. Disable selector when loading
5. Include type in API request body

**API Request Update**:
- POST /visualize with body: `{ question, visualization_type: visualizationType }`
- Response includes type field
- Polling endpoint unchanged

**Rendering Logic**:
- Pass type to VisualizationRenderer component
- Component switches between MindmapRenderer and Mermaid based on type
- Show appropriate loading messages

**Additional UI Enhancements**:
- Add "Export" button (PNG/SVG)
- Show visualization metadata (node count, depth)
- Add "Try another type" button after generation

### 4.3 Create Advanced Options Panel (Optional)

**Create `components/ui/visualization-options.tsx`**:
- Collapsible panel for power users
- Complexity slider: Simple | Balanced | Detailed
- Max depth number input (2-6)
- Style presets dropdown
- Pass options to backend in API request

---

## Task 5: Fix Environment Variable Issues (Day 10)

### 5.1 Frontend Configuration

**Update `docker-compose.yml`**:
- Change: `NEXT_PUBLIC_API_URL` → `NEXT_PUBLIC_API_BASE_URL`
- Value remains: `http://localhost:8000`

**Update `frontend/app/page.tsx`**:
- Verify usage: `const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'`
- Remove any fallback API path logic
- Ensure consistent URL construction

### 5.2 Backend Configuration

**Verify `backend/.env`**:
- Confirm `GEMINI_API_KEY` is set
- Add `LOG_LEVEL=INFO` for better debugging
- Add `MAX_WORKERS=4` for concurrent job processing

**Update `backend/app/core/config.py`**:
- Use Pydantic BaseSettings for validation
- Add validators for required fields
- Raise clear errors if GEMINI_API_KEY missing

### 5.3 Update Main Backend Endpoint

**Modify `backend/app/main.py`**:

**Request/Response Models**:
- Create `VisualizationRequest` Pydantic model: question, visualization_type, options
- Create `VisualizationResponse` model: job_id
- Create `JobStatusResponse` model: status, type, content, metadata, error

**Update Endpoints**:

1. `POST /visualize`:
   - Accept VisualizationRequest body
   - Validate visualization_type against supported types
   - Create job with type and options
   - Call llm_service.generate_visualization in background
   - Return job_id immediately

2. `GET /visualize/{job_id}`:
   - Return JobStatusResponse with all fields
   - Include visualization type and metadata
   - Return 404 if job_id not found

**Job Storage Updates**:
- Store: job_id, status, type, content, metadata, error, created_at
- Add job expiry: remove after 1 hour
- Add cleanup task for expired jobs

---

## Testing Strategy

### Unit Tests

**Backend** (`tests/test_strategies.py`):
- Test MindmapStrategy.generate() with sample questions
- Test FlowchartStrategy.generate() with sample questions
- Test JSON to markdown conversion
- Test JSON to Mermaid conversion
- Test domain detection accuracy
- Test validation methods
- Mock Gemini API calls

**Frontend** (`__tests__/components/`):
- Test VisualizationTypeSelector selection changes
- Test VisualizationRenderer type switching
- Test MindmapRenderer with sample markdown
- Test loading states and error handling

### Integration Tests

**API Tests** (`tests/test_api.py`):
- Test POST /visualize with different types
- Test job status polling
- Test error responses (invalid type, missing API key)
- Test concurrent job processing

**E2E Tests** (`tests/e2e/`):
- Use Playwright or Cypress
- Test full flow: select type → enter question → see result
- Test switching between types
- Test error scenarios
- Test responsive design

### Manual Testing Checklist

- [ ] Flowchart generation works as before
- [ ] Mindmap generation produces valid markdown
- [ ] Type selector is responsive and accessible
- [ ] Switching types clears previous results
- [ ] Loading states display correctly
- [ ] Error messages are user-friendly
- [ ] Dark mode works for both visualization types
- [ ] Export functionality works (if implemented)
- [ ] Different complexity levels produce appropriate output
- [ ] Domain detection chooses correct prompts

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing (unit, integration, e2e)
- [ ] Environment variables documented
- [ ] Docker images build successfully
- [ ] Database migrations ready (if added persistence)
- [ ] API documentation updated
- [ ] Performance benchmarks acceptable (<5s for simple visualizations)

### Deployment Steps

1. **Build and Test Locally**:
   ```bash
   docker compose down
   docker compose build --no-cache
   docker compose up
   ```

2. **Smoke Test**:
   - Test flowchart generation
   - Test mindmap generation
   - Test error handling
   - Test type switching

3. **Deploy to Staging**:
   - Push to staging environment
   - Run automated test suite
   - Manual QA testing
   - Load testing with sample queries

4. **Deploy to Production**:
   - Blue-green deployment or rolling update
   - Monitor logs for errors
   - Check metrics (response time, error rate)
   - Verify both visualization types working

### Post-Deployment

- [ ] Monitor error rates (target: <1%)
- [ ] Monitor response times (target: <5s p95)
- [ ] Monitor API usage patterns
- [ ] Collect user feedback
- [ ] Document any issues in incident log

### Rollback Plan

If critical issues found:
1. Revert to previous Docker images
2. Restore previous docker-compose.yml
3. Verify old functionality works
4. Investigate issues in staging
5. Plan hotfix or next sprint

---

## Success Criteria

### Functional Requirements Met
- ✅ Users can select between flowchart and mindmap
- ✅ Mindmaps render correctly with Markmap
- ✅ Flowcharts still work as before
- ✅ Backend uses strategy pattern for extensibility
- ✅ Environment variables configured correctly

### Quality Metrics
- Code coverage: >80%
- No critical bugs in production
- Performance: 95th percentile <5 seconds
- User satisfaction: Positive feedback on new feature

### Technical Debt Addressed
- ✅ In-memory storage documented for next sprint
- ✅ Strategy pattern enables easy addition of new types
- ✅ Configuration issues resolved
- ✅ Code is modular and testable

---

## Next Steps (Sprint 3-4 Preview)

### Immediate Improvements
1. Add third visualization type (timeline or network diagram)
2. Implement Redis for job queue
3. Add PostgreSQL for visualization history
4. Add user authentication

### Future Enhancements
1. AI-powered type suggestion
2. Interactive editing of generated visualizations
3. Collaboration features (sharing, comments)
4. Export to multiple formats (PNG, SVG, PDF)
5. Template library for common use cases
6. API endpoints for programmatic access

---

## Notes for Development Team

### Key Architectural Decisions

1. **Strategy Pattern**: Chosen for extensibility. Adding new visualization types requires:
   - New strategy class implementing VisualizationStrategy
   - Registration in VisualizationFactory
   - Frontend renderer component

2. **JSON-First Approach**: LLM generates JSON, backend converts to target format. This ensures:
   - Consistent, parseable output
   - Easy validation and error handling
   - Flexibility in output format

3. **Frontend Dynamic Imports**: Markmap imported dynamically to avoid SSR issues with browser-only libraries

4. **Domain Detection**: Simple keyword matching. Consider ML-based classification in future for better accuracy

### Common Pitfalls to Avoid

1. **LLM Output Parsing**: Always use regex to extract JSON from markdown code blocks
2. **Async Job Management**: Ensure proper cleanup of completed jobs
3. **Frontend Hydration**: Use `useState` to check mounting before rendering visualizations
4. **Docker Environment Variables**: Test with both docker-compose and manual Docker runs
5. **Depth Limits**: Enforce max_depth in backend to prevent infinite recursion

### Resources

- Markmap Documentation: https://markmap.js.org/
- Mermaid Documentation: https://mermaid.js.org/
- Google Gemini API: https://ai.google.dev/docs
- Strategy Pattern: https://refactoring.guru/design-patterns/strategy

---

## Questions & Support

For implementation questions:
1. Check existing flowchart implementation for patterns
2. Review strategy pattern documentation
3. Test with simple examples first
4. Use verbose logging during development

Common issues:
- **Markmap not rendering**: Check console for import errors, verify dynamic import setup
- **LLM returning invalid JSON**: Improve prompt clarity, add JSON schema validation
- **Type selector not working**: Verify state management and prop passing
- **Backend errors**: Check Gemini API key, review error logs, verify JSON parsing

---

**End of Sprint 1-2 Implementation Guide**