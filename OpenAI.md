# OpenAI API Overview

This document summarizes the standard OpenAI API framework, focusing on the endpoints and data formats most relevant to LLM-based applications and agentic coding assistants.


## Major OpenAI API Endpoints

### Models
- `/v1/models` — List available models
- `/v1/models/{model}` — Retrieve model details

### Completions
- `/v1/completions` — Text completion (legacy, GPT-3 style)
- `/v1/chat/completions` — Chat-based completion (GPT-3.5/4 style)

### Embeddings
- `/v1/embeddings` — Generate vector embeddings for text

### Moderations
- `/v1/moderations` — Content moderation for safety

### Files
- `/v1/files` — Upload, list, and manage files
- `/v1/files/{file_id}` — Retrieve or delete a file
- `/v1/files/{file_id}/content` — Download file content

### Fine-tuning
- `/v1/fine_tuning/jobs` — Create and manage fine-tuning jobs
- `/v1/fine_tuning/jobs/{job_id}` — Retrieve fine-tune job status
- `/v1/fine_tuning/jobs/{job_id}/events` — List fine-tune job events

### Images
- `/v1/images/generations` — Create images from text
- `/v1/images/edits` — Edit images
- `/v1/images/variations` — Create image variations

### Audio
- `/v1/audio/transcriptions` — Speech-to-text (transcribe audio)
- `/v1/audio/translations` — Translate audio
- `/v1/audio/speech` — Text-to-speech

### Threads & Messages (Assistants API)
- `/v1/threads` — Manage conversation threads
- `/v1/threads/{thread_id}/messages` — Manage messages in a thread

### Runs (Assistants API)
- `/v1/threads/{thread_id}/runs` — Manage runs (executions) for a thread

### Batches
- `/v1/batches` — Create and manage batch jobs

### Evals
- `/v1/evals` — Manage evaluation jobs

### Others
- `/v1/answers` — (Deprecated) Q&A endpoint
- `/v1/classifications` — (Deprecated) Classification endpoint

---
**Note:** Not all endpoints are available for every account or model. Some (like Assistants API, Batches, Evals) may be in beta or require special access.

For the latest and most complete list, see the [OpenAI API Reference](https://platform.openai.com/docs/api-reference).

## Data Formats

### Chat Message Object
```
{
  "role": "system" | "user" | "assistant",
  "content": "..."
}
```

### Tool/Function Calling (chat/completions)
- `tools`: List of tool schemas (OpenAPI-style function definitions)
- `tool_choice`: "none", "auto", or specific tool name
- Response may include `tool_calls` in the assistant message

### Streaming
- If `stream: true`, responses are sent as Server-Sent Events (SSE)
- Each event contains a partial message (delta)

## References
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)

---
This document covers the standard OpenAI API endpoints and formats. For custom agent protocols (like /v1/responses), see your project-specific documentation.