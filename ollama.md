# Ollama API Documentation

This document summarizes the REST API for [Ollama](https://github.com/ollama/ollama), a local LLM server supporting a wide range of models and features. For full details, see the [official API docs](https://github.com/ollama/ollama/blob/main/docs/api.md).

## Base URL

```
http://localhost:11434
```

## Endpoints

### 1. Generate a Completion
- **POST /api/generate**
- Generate a response for a prompt with a specified model.
- Supports streaming and non-streaming responses.
- **Parameters:**
  - `model` (required): Model name
  - `prompt`: Text prompt
  - `suffix`: Text after the model response
  - `images`: List of base64-encoded images (for multimodal models)
  - `think`: For thinking models
  - `format`: `json` or JSON schema for structured output
  - `options`: Model parameters (temperature, etc.)
  - `system`: System message
  - `template`: Prompt template
  - `stream`: If `false`, returns a single response object
  - `raw`: If `true`, disables prompt formatting
  - `keep_alive`: How long the model stays loaded
  - `context`: For conversational memory (deprecated)
- **Example (streaming):**
```json
POST /api/generate
{
  "model": "llama3.2",
  "prompt": "Why is the sky blue?"
}
```
- **Response (stream):**
```json
{
  "model": "llama3.2",
  "created_at": "...",
  "response": "The",
  "done": false
}
```
Final response includes stats and context.

### 2. Generate a Chat Completion
- **POST /api/chat**
- Chat with a model using a message history.
- Supports tool calling, structured outputs, streaming.
- **Parameters:**
  - `model` (required): Model name
  - `messages`: Array of message objects (`role`, `content`, etc.)
  - `tools`: List of tools (for tool calling)
  - `think`: For thinking models
  - `format`: `json` or JSON schema
  - `options`: Model parameters
  - `stream`: If `false`, returns a single response object
  - `keep_alive`: How long the model stays loaded
- **Example:**
```json
POST /api/chat
{
  "model": "llama3.2",
  "messages": [
    { "role": "user", "content": "Why is the sky blue?" }
  ]
}
```
- **Response (stream):**
```json
{
  "model": "llama3.2",
  "created_at": "...",
  "message": { "role": "assistant", "content": "The" },
  "done": false
}
```

### 3. Create a Model
- **POST /api/create**
- Create a new model from another model, GGUF file, or safetensors directory.
- **Parameters:**
  - `model`: Name of new model
  - `from`: Source model
  - `files`: Dictionary of file names to SHA256 digests
  - `adapters`: LORA adapters
  - `template`, `license`, `system`, `parameters`, `messages`, `stream`, `quantize`
- **Example:**
```json
POST /api/create
{
  "model": "mario",
  "from": "llama3.2",
  "system": "You are Mario from Super Mario Bros."
}
```

### 4. List Local Models
- **GET /api/tags**
- List models available locally.
- **Response:**
```json
{
  "models": [ { "name": "llama3.2:latest", ... } ]
}
```

### 5. Show Model Information
- **POST /api/show**
- Show details about a model.
- **Parameters:**
  - `model`: Model name
  - `verbose`: If `true`, returns full data

### 6. Copy a Model
- **POST /api/copy**
- Copy a model to a new name.
- **Parameters:**
  - `source`: Source model
  - `destination`: New model name

### 7. Delete a Model
- **DELETE /api/delete**
- Delete a model and its data.
- **Parameters:**
  - `model`: Model name

### 8. Pull a Model
- **POST /api/pull**
- Download a model from the Ollama library.
- **Parameters:**
  - `model`: Model name
  - `insecure`, `stream`

### 9. Push a Model
- **POST /api/push**
- Upload a model to a model library.
- **Parameters:**
  - `model`: Model name
  - `insecure`, `stream`

### 10. Generate Embeddings
- **POST /api/embed**
- Generate embeddings from a model.
- **Parameters:**
  - `model`: Model name
  - `input`: Text or list of texts
  - `truncate`, `options`, `keep_alive`, `dimensions`
- **Response:**
```json
{
  "model": "all-minilm",
  "embeddings": [[...], [...]]
}
```

### 11. List Running Models
- **GET /api/ps**
- List models currently loaded into memory.
- **Response:**
```json
{
  "models": [ { "name": "mistral:latest", ... } ]
}
```

### 12. Version
- **GET /api/version**
- Get the Ollama server version.
- **Response:**
```json
{
  "version": "0.5.1"
}
```

## Conventions
- **Model names:** `model:tag` format (e.g., `llama3:70b`)
- **Durations:** Returned in nanoseconds
- **Streaming:** Most endpoints support streaming JSON responses

## Features
- Supports completions, chat, tool calling, structured outputs, multimodal (images), embeddings, model management, quantization, and more.
- Compatible with many open-source models (Llama, Gemma, Mistral, Qwen, etc.)

## References
- [Ollama API Docs](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Ollama Homepage](https://ollama.com/)

---
For advanced usage, see the full API documentation and [Modelfile parameters](https://github.com/ollama/ollama/blob/main/docs/modelfile.mdx#valid-parameters-and-values).
