# Sprint 4C: Asynchronous Orchestration & Jobs

**Goal:** Transform the BDIS pipeline into a scalable, asynchronous engine using Celery and Redis, while maintaining strict Clean Architecture boundaries.

## 🎯 Deliverables

1.  **Orchestration Logic (`ProcessingPipeline`):**
    *   Implement the orchestrator that coordinates `Sanitizer -> Extractor -> Normalizer -> Validator -> Evaluator`.
    *   Ensure the orchestrator interacts only with **Ports**, never concrete Adapters.

2.  **Infrastructure: Redis & Celery:**
    *   Add Redis to `docker-compose.yml`.
    *   Initialize Celery workers in `src/bdis/frameworks/workers/celery_app.py`.

3.  **Job Lifecycle API:**
    *   Implement `POST /jobs` to enqueue a document.
    *   Implement `GET /jobs/{id}` to poll for results.
    *   Ensure the API maps Domain Objects to serializable DTOs.

4.  **Observability & Traceability:**
    *   Implement structured JSON logging with a unique `trace_id` for every job.
    *   Track timing for each pipeline step to identify bottlenecks.

## ✅ Definition of Done
- A document can be uploaded via the API and processed in the background by a Celery worker.
- Logs show a clear "Trace ID" trail through every step of the pipeline.
- The system handles job failures gracefully, updating the status to `FAILED` with appropriate error details.
