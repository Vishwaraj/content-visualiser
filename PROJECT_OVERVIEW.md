# Project Overview: Content Visualizer

## 1. Introduction

The "Content Visualizer" is a full-stack web application designed to take a user's natural language question or prompt and generate a conceptual flowchart in the form of a Mermaid diagram. It leverages Google's Gemini Large Language Model (LLM) to interpret the user's input and structure the visual output.

## 2. Architecture & Data Flow

The application follows an asynchronous job pattern to handle the potentially long-running LLM requests, providing a responsive user experience.

1.  **User Input**: The frontend captures a user's question through a simple input form.
2.  **Request Initiation**: The frontend sends a POST request containing the user's question to the backend's `/visualize` endpoint.
3.  **Job Creation**: The backend immediately creates a unique job, stores its state (currently in an in-memory dictionary, meaning job history is lost on service restart), and returns a `job_id` to the frontend.
4.  **Asynchronous Processing**: In the background, the backend's LLM service communicates with the Google Gemini API. It sends a prompt designed to elicit a structured JSON representation of a flowchart. This JSON-first approach ensures robust and predictable output from the LLM.
5.  **Mermaid Diagram Generation**: Upon receiving the JSON response, the backend deterministically converts this JSON into a valid Mermaid diagram string.
6.  **Frontend Polling**: The frontend continuously polls the backend's `/visualize/{job_id}` endpoint using the received `job_id` to check the status of the visualization job.
7.  **Result Rendering**: Once the job is marked as complete and the Mermaid code is available, the frontend retrieves it and uses the `mermaid.js` library to render the diagram as an interactive SVG directly in the user's browser.

## 3. Technologies Used

### 3.1 Frontend
*   **Framework**: Next.js (React)
*   **Styling**: Tailwind CSS for utility-first styling.
*   **Theming**: Custom auto dark mode implementation based on system preferences.
*   **Diagram Rendering**: `mermaid.js` for converting Mermaid syntax into SVG diagrams.
*   **Other**: `clsx` for conditional class names, `lucide-react` for icons.

### 3.2 Backend
*   **Framework**: FastAPI for building robust and performant APIs.
*   **Language**: Python
*   **LLM Integration**: `google-generativeai` library for interacting with the Google Gemini API.
*   **Asynchronous Tasks**: Standard Python `asyncio` for managing concurrent operations.
*   **Environment Management**: `python-dotenv` for loading environment variables.

### 3.3 Orchestration
*   **Containerization**: Docker for packaging applications into portable containers.
*   **Multi-container Management**: Docker Compose for defining and running multi-container Docker applications.

## 4. Key Components and Their Responsibilities

### 4.1 Frontend (`frontend/`)

*   `app/page.tsx`: The primary entry point for the application's user interface. It manages user input, triggers backend API calls, handles state for job status and diagram display, and renders the final Mermaid diagram.
*   `app/layout.tsx`: Defines the root HTML structure and includes the `ThemeSetter` component for dynamic theme management.
*   `app/globals.css`: Contains global CSS styles, Tailwind CSS imports, and custom CSS variables for managing the application's theming (light/dark mode).
*   `components/theme-setter.tsx`: A client-side React component responsible for detecting the user's system color scheme preference and applying the `dark` class to the `<html>` element accordingly.
*   `components/ui/*.tsx`: Reusable UI components (e.g., Button, Card, Label, Textarea).

### 4.2 Backend (`backend/`)

*   `app/main.py`: The FastAPI application instance. It defines the main API routes:
    *   `POST /visualize`: Initiates a new visualization job.
    *   `GET /visualize/{job_id}`: Allows the frontend to poll for the status and results of a specific job.
    *   Manages the in-memory job queue (`_jobs`).
*   `app/services/llm_service.py`: Encapsulates the logic for interacting with the Google Gemini LLM. It's responsible for constructing prompts, sending requests to the Gemini API, and processing the LLM's structured JSON output to generate Mermaid diagram code.
*   `app/core/config.py`: Handles application configuration, including loading the `GEMINI_API_KEY` from environment variables.

## 5. Setup and Running the Project

To set up and run the "Content Visualizer" project locally:

1.  **Prerequisites**: Ensure you have Docker and Docker Compose installed on your system. You will also need a Google Gemini API key.
2.  **Environment Variables**:
    *   Create a `.env` file in the `backend/` directory with your Gemini API key:
        ```
        GEMINI_API_KEY=YOUR_GEMINI_API_KEY
        ```
3.  **Build and Run**: Navigate to the root directory of the project (where `docker-compose.yml` is located) and run:
    ```bash
    docker compose up --build
    ```
    This command will build the Docker images for both the frontend and backend services and start them.
4.  **Access the Application**:
    *   Frontend: Typically available at `http://localhost:3000`
    *   Backend API: Typically available at `http://localhost:8000`

## 6. Identified Discrepancies/Improvements

During the codebase investigation, the following points were noted:

*   **`docker-compose.yml` Environment Variable Typo**: The `docker-compose.yml` file sets an environment variable named `NEXT_PUBLIC_API_URL` for the frontend. However, the frontend code (`frontend/app/page.tsx`) expects this variable to be named `NEXT_PUBLIC_API_BASE_URL`. Despite this, the application functions because the frontend falls back to a default `http://localhost:8000` and ignores an incorrect API path set in Docker. Correcting this variable name is recommended for clarity and proper configuration adherence.
*   **In-memory Job Storage**: The backend currently uses an in-memory dictionary (`_jobs` in `main.py`) to store job statuses and results. This means that all job history and pending results will be lost if the backend service is restarted. For a production-ready application, this should be replaced with a persistent storage solution (e.g., a database, Redis, or a dedicated message queue/job store).
