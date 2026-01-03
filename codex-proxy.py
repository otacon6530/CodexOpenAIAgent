# Python proxy between Codex CLI and OpenAI API (vllm)
# Adds full /v1/responses translation for Codex Agent Protocol

from fastapi import FastAPI, Request, Response
import httpx
import uvicorn
import os
import json
from typing import Dict

app = FastAPI()

# codex-proxy.py
# Python proxy between Codex CLI and an OpenAI-compatible API (vLLM/Ollama).
# - Translates Codex /v1/responses -> OpenAI /v1/chat/completions
# - Wraps OpenAI responses back into Codex Agent Protocol format

from fastapi import FastAPI, Request, Response
import httpx
import uvicorn
import os
import json
from typing import Dict, Any

app = FastAPI()

# Base URL for your vLLM / Ollama / other OpenAI-compatible server
# Example: export VLLM_API_URL="http://apple.stephensdev.com:8000"
target_openai_url = os.environ.get("VLLM_API_URL", "http://apple.stephensdev.com:8000")

# Model to send to vLLM/Ollama
MODEL_NAME = "Qwen/Qwen2.5-Coder-7B-Instruct-AWQ"  # change to your model


# -----------------------------
#  Codex -> OpenAI translator
# -----------------------------
def codex_to_openai(codex_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Codex Agent Protocol payload (for /v1/responses)
    into a standard OpenAI /v1/chat/completions request.
    """
    messages = []

    # Codex sends conversation history inside "input": [...]
    for item in codex_payload.get("input", []):
        if item.get("type") != "message":
            continue

        role = item.get("role", "user")
        content_blocks = item.get("content", [])

        text_parts = []
        for block in content_blocks:
            # We care about the text-bearing blocks
            if block.get("type") in ("input_text", "output_text"):
                text_parts.append(block.get("text", ""))

        text = "\n".join(text_parts).strip()
        if text:
            messages.append({"role": role, "content": text})

    if not messages:
        # Fallback: if nothing parsed, at least send *something*
        messages = [{"role": "user", "content": "No usable content found in Codex input."}]

    return {
        "model": MODEL_NAME,
        "messages": messages,
    }


# -----------------------------
#  OpenAI -> Codex translator
# -----------------------------
def openai_to_codex(openai_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert an OpenAI /v1/chat/completions response
    back into a minimal Codex Agent Protocol-style response.
    """
    # If vLLM returned an error or unexpected shape, surface it to Codex instead of crashing
    if "choices" not in openai_response:
        error_text = json.dumps(openai_response, indent=2)
        return {
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "output_text",
                            "text": f"[LLM ERROR]\n{error_text}",
                        }
                    ],
                }
            ]
        }

    # Normal OpenAI chat response
    choice = openai_response["choices"][0]
    message = choice.get("message", {})
    text = message.get("content", "")

    return {
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": text,
                    }
                ],
            }
        ]
    }


# -----------------------------
#  Codex /v1/responses endpoint
# -----------------------------
@app.post("/v1/responses")
async def proxy_responses(request: Request):
    """
    Main entrypoint for Codex Agent Protocol calls.
    Codex posts here; we translate and forward to vLLM/Ollama.
    """
    codex_payload = await request.json()

    # Translate Codex -> OpenAI
    openai_payload = codex_to_openai(codex_payload)

    # Debug logging (optional)
    # print("Codex payload:", json.dumps(codex_payload, indent=2))
    # print("OpenAI payload:", json.dumps(openai_payload, indent=2))

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{target_openai_url}/v1/chat/completions",
            json=openai_payload,
        )

    # Try to parse JSON; if it fails, wrap the raw text as an error
    try:
        llm_json = resp.json()
    except Exception:
        llm_json = {
            "error": {
                "status_code": resp.status_code,
                "text": resp.text,
            }
        }

    codex_output = openai_to_codex(llm_json)
    return codex_output


# -----------------------------
#  Existing /v1/completions handler (from your original)
# -----------------------------
OPENAI_COMPLETION_FIELDS = {
    "model",
    "prompt",
    "suffix",
    "max_tokens",
    "temperature",
    "top_p",
    "n",
    "stream",
    "logprobs",
    "echo",
    "stop",
    "presence_penalty",
    "frequency_penalty",
    "best_of",
    "logit_bias",
    "user",
}


def filter_openai_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove non-OpenAI fields from the request body."""
    return {k: v for k, v in data.items() if k in OPENAI_COMPLETION_FIELDS}


@app.post("/v1/completions")
async def proxy_completions(request: Request):
    body = await request.json()
    filtered_body = filter_openai_fields(body)

    # Catalog extra fields for inspection/debugging
    extra_fields = {k: v for k, v in body.items() if k not in OPENAI_COMPLETION_FIELDS}
    if extra_fields:
        with open("extra_codex_fields.log", "a") as logf:
            logf.write(json.dumps({"extra": extra_fields, "full": body}) + "\n")

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{target_openai_url}/v1/completions", json=filtered_body)

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
    )


# -----------------------------
#  Catch-all proxy
# -----------------------------
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all_proxy(request: Request, path: str):
    method = request.method
    url = f"{target_openai_url}/{path}"
    headers = dict(request.headers)
    headers.pop("host", None)
    body = await request.body()

    async with httpx.AsyncClient() as client:
        resp = await client.request(method, url, headers=headers, content=body)

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5555)
