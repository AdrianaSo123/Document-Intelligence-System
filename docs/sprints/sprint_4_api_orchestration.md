# Sprint 4: Web API & Asynchronous Orchestration

**Goal:** Expose the architecture to the outside world, ensuring the system remains responsive under heavy load.

## 🎯 Deliverables

1. **FastAPI Controllers:**
   - Implement POST `/upload` to accept files.
   - Implement GET `/status/{job_id}` to retrieve parsed insights.

2. **Message Queue Architecture:**
   - Setup Redis and a Celery worker.
   - Configure the POST `/upload` endpoint to save the file and enqueue a job instead of blocking.

3. **Dependency Injection:**
   - Wire the FastAPI dependency injection system to pass the `OpenAIExtractor` and `SqliteDocumentRepository` into the `ProcessDocumentUseCase`.

4. **Enterprise Observability:**
   - Integrate Sentry for exception tracking (especially to catch silent LLM failures).
   - Integrate LangSmith or Helicone for tracing LLM latency and costs.

5. **Testing & Deployment Docs:**
   - Write End-to-End (E2E) tests hitting the `/upload` endpoint, polling the status, and verifying the final state.
   - Create Dockerfiles and `docker-compose.yml` to spin up the API, Celery, and Redis together.

## ✅ Definition of Done
- A user can upload a PDF, instantly receive a `job_id`, and ping the status endpoint to get their validated Business Insights JSON.
- The system survives a server restart without losing pending jobs.
