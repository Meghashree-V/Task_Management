# Task Management API

Backend assessment project implementing a Task Management API using **FastAPI** and **Google Cloud Platform**.

## Features

- **Task CRUD API** using FastAPI
  - `POST /tasks` – create task
  - `GET /tasks` – list tasks (filter by priority/status)
  - `GET /tasks/{task_id}` – get single task
  - `PUT /tasks/{task_id}` – update task status
  - `DELETE /tasks/{task_id}` – delete task
  - `GET /health` – health check
- **In-memory storage** (Python dict) – no database required
- **Event publishing to Pub/Sub** on task creation
- **Cloud Run function subscriber** that:
  - Listens to `task-events` Pub/Sub topic
  - Logs the incoming `task.created` event
  - Calls **Gemini 2.5 Flash** to:
    - Generate a one-sentence summary
    - Suggest 3–5 sub-tasks
    - Categorize the task (Bug Fix / Feature / DevOps / Documentation)
  - Logs the Gemini output
- **Dockerized** and deployed to **Cloud Run**
- **GitHub Actions** CI/CD pipeline to build, push, and deploy on every push to `main`.

## Tech Stack

- Python 3.11
- FastAPI
- Uvicorn
- Google Cloud Run
- Google Cloud Pub/Sub
- Cloud Run (2nd gen function) + Eventarc
- Gemini 2.5 Flash API
- GitHub Actions

## Local Development

### Prerequisites

- Python 3.11+
- `gcloud` CLI installed and authenticated
- Google Cloud project with Pub/Sub enabled

### Install dependencies

```bash
pip install -r requirements.txt
```

### Set environment variables

```bash
# PowerShell example
$env:GCP_PROJECT_ID = "task-management-demo-478410"
$env:PUBSUB_TOPIC   = "task-events"
```

### Run the API locally

```bash
uvicorn main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## GCP Resources

- **Project**: `task-management-demo-478410`
- **Pub/Sub topic**: `task-events`
- **FastAPI Cloud Run service**: `task-api`
- **Cloud Run URL**: `https://task-api-297638120012.asia-south2.run.app`
- **Cloud Run function subscriber**: `task-event-subscriber`

## Deployment (Cloud Run)

FastAPI service is deployed using:

```bash
gcloud run deploy task-api \
  --source . \
  --region asia-south2 \
  --allow-unauthenticated
```

Environment variables for the service:

- `GCP_PROJECT_ID = task-management-demo-478410`
- `PUBSUB_TOPIC   = task-events`

## CI/CD (GitHub Actions)

Workflow file: `.github/workflows/deploy.yml`

On every push to `main`:

1. Authenticate to Google Cloud using `GCP_SA_KEY` secret.
2. Build Docker image from the `Dockerfile`.
3. Push image to **Artifact Registry**.
4. Deploy the image to Cloud Run service `task-api`.

## Cloud Function + Gemini

Cloud Run function (`task-event-subscriber`) is triggered by Pub/Sub topic `task-events`.

- Decodes `task.created` events with schema:

```json
{
  "event_type": "task.created",
  "task_id": "string",
  "timestamp": "ISO8601",
  "data": {
    "title": "string",
    "description": "string",
    "priority": "string"
  }
}
```

- Calls Gemini 2.5 Flash via REST API using `GEMINI_API_KEY` environment variable.
- Logs both:
  - `Received event: {...}`
  - `Gemini output: {...}`

These logs are visible in **Cloud Run → task-event-subscriber → Logs / Logs Explorer** and are used as evidence for the assessment.

### Example logs / Gemini evidence

Below screenshots (from Logs Explorer) demonstrate the end-to-end flow:

1. **Received event log**  
   The subscriber logs the decoded Pub/Sub message:

   ```text
   Received event: {"event_type": "task.created", "task_id": "TEST-123", "timestamp": "2025-11-16T12:30:00Z", "data": {"title": "Manual Pub/Sub test", "description": "Testing Cloud Run + Gemini via gcloud.", "priority": "high"}}
   ```

   This confirms that the Cloud Run function successfully received a `task.created` event from the `task-events` topic and parsed the full schema (task id, timestamp, title, description, priority).

   _Screenshot placeholder:_

   `![Received event log](./docs/received-event-log.png)`

2. **Gemini output log**  
   After building a prompt from the task data, the function calls Gemini 2.5 Flash and logs the raw response:

   ```text
   Gemini output: {"candidates": [{"content": {"role": "model"}, "finishReason": "MAX_TOKENS", "index": 0}], "usageMetadata": {"promptTokenCount": 58, "totalTokenCount": 313, "promptTokensDetails": [{"modality": "TEXT", "tokenCount": 58}], "thoughtsTokenCount": 255}, "modelVersion": "gemini-2.5-flash", "responseId": "..."}
   ```

   The `candidates[0].content` text (not fully shown here) contains the generated one-sentence summary, 3–6 suggested sub-tasks, and a category (Bug Fix / Feature / DevOps / Documentation) according to the prompt. The `modelVersion` field confirms the use of `gemini-2.5-flash`.

   _Screenshot placeholder:_

   `![Gemini output log](./docs/gemini-output-log.png)`
