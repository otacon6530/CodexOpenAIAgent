# OpenAI Responses API Documentation

This document summarizes the OpenAI Responses API, which provides advanced, stateful model interactions supporting text, image, tool calls, and multi-turn conversations.

## Endpoints

### 1. Create a Model Response
- **POST** `/v1/responses`
- Generates a model response from text, image, or file input.
- Supports system instructions, tool calls, reasoning, streaming, and more.
- **Request body fields:**
  - `model`: Model ID (e.g., "gpt-4o")
  - `input`: Text, image, or file input (string or array)
  - `instructions`: System/developer message
  - `tools`: Array of tools (built-in, MCP, or custom functions)
  - `tool_choice`: How the model selects tools
  - `stream`: Boolean, enables SSE streaming
  - `conversation`: Conversation object or ID for stateful interactions
  - `previous_response_id`: For multi-turn conversations
  - `max_output_tokens`, `max_tool_calls`, `temperature`, `top_p`, `truncation`, etc.
  - `metadata`: Key-value pairs for tracking
  - `store`: Boolean, whether to store the response
  - `service_tier`: Processing tier (auto, default, flex, priority)

### 2. Get a Model Response
- **GET** `/v1/responses/{response_id}`
- Retrieves a previously generated response by ID.
- **Query params:**
  - `include`: Additional fields to include
  - `stream`: If true, streams the response

### 3. Delete a Model Response
- **DELETE** `/v1/responses/{response_id}`
- Deletes a response by ID.

### 4. Cancel a Response
- **POST** `/v1/responses/{response_id}/cancel`
- Cancels a background response (created with `background: true`).

### 5. Compact a Response
- **POST** `/v1/responses/compact`
- Compacts a conversation, returning encrypted/opaque items to manage context window size.

### 6. List Input Items
- **GET** `/v1/responses/{response_id}/input_items`
- Lists input items used to generate a response.

### 7. Get Input Token Counts
- **POST** `/v1/responses/input_tokens`
- Returns token counts for a given input and model.

## Response Object Structure
```
{
  "id": "resp_...",
  "object": "response",
  "created_at": 1741476542,
  "status": "completed",
  "error": null,
  "instructions": "...",
  "model": "gpt-4o-2024-08-06",
  "output": [
    {
      "type": "message",
      "id": "msg_...",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "...",
          "annotations": []
        }
      ]
    }
  ],
  "parallel_tool_calls": true,
  "previous_response_id": null,
  "reasoning": { ... },
  "store": true,
  "temperature": 1.0,
  "tool_choice": "auto",
  "tools": [],
  "top_p": 1.0,
  "truncation": "disabled",
  "usage": {
    "input_tokens": 36,
    "output_tokens": 87,
    "total_tokens": 123
  },
  "user": null,
  "metadata": {}
}
```

## Features
- Supports text, image, and file inputs
- Multi-turn conversations via `conversation` or `previous_response_id`
- Built-in tools (web search, file search, code interpreter, etc.)
- MCP tools (third-party connectors)
- Custom function calling
- Reasoning and structured outputs
- Streaming via SSE
- Context management and compaction

## References
- [OpenAI Responses API Reference](https://platform.openai.com/docs/api-reference/responses)
- [Conversation State](https://platform.openai.com/docs/guides/conversation-state)
- [Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Tools](https://platform.openai.com/docs/guides/tools)

---
This document covers the OpenAI Responses API, which is more advanced than the standard chat/completions API and is designed for agentic, tool-augmented, and multi-modal workflows.
