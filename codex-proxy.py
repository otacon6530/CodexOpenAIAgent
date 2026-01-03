# Logging-only proxy for Codex/OpenAI APIs
# This version logs all incoming requests and outgoing responses, but does not translate or modify any API payloads.


import argparse
import logging
from fastapi import FastAPI, Request, Response
import httpx
import uvicorn
import os
import json
from tool import run_tool

# Global debug flag
DEBUG_MODE = False

# Set up logger
logger = logging.getLogger("codex-proxy-logging")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("codex-proxy-logging.log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

app = FastAPI()

# Base URL for your OpenAI-compatible server
# Example: export VLLM_API_URL="http://localhost:11434"
target_openai_url = os.environ.get("VLLM_API_URL", "http://apple.stephensdev.com:11434")


# Tool-call aware proxy
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def tool_proxy(request: Request, path: str):
    method = request.method
    url = f"{target_openai_url}/{path}"
    headers = dict(request.headers)
    headers.pop("host", None)
    body = await request.body()

    logger.info(f"Incoming {method} {request.url.path} headers: {json.dumps(headers)}")
    if body:
        try:
            logger.info(f"Incoming {method} {request.url.path} body: {body.decode(errors='replace')}")
        except Exception:
            logger.info(f"Incoming {method} {request.url.path} body: <binary>")

    # Only intercept POSTs to /v1/chat/completions or /v1/responses for tool handling
    if method == "POST" and path in ["v1/chat/completions", "v1/responses"]:
        try:
            json_body = None
            try:
                json_body = json.loads(body)
            except Exception:
                pass
            async with httpx.AsyncClient(timeout=6000) as client:
                resp = await client.request(method, url, headers=headers, content=body)
            # Try to parse response as JSON
            try:
                resp_json = resp.json()
            except Exception:
                resp_json = None
            # Check for tool calls in OpenAI function/tool calling format
            tool_calls = None
            if resp_json:
                # OpenAI: choices[0].message.tool_calls
                choices = resp_json.get("choices")
                if choices and "message" in choices[0]:
                    tool_calls = choices[0]["message"].get("tool_calls")
            if tool_calls:
                tool_results = []
                for call in tool_calls:
                    tool_name = call.get("function", {}).get("name") or call.get("name")
                    arguments = call.get("function", {}).get("arguments") or call.get("arguments")
                    # Arguments may be a JSON string
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except Exception:
                            arguments = {}
                    result = run_tool(tool_name, arguments or {})
                    tool_results.append({
                        "tool_call_id": call.get("id"),
                        "output": result["output"]
                    })
                # Compose a tool message to send back to the LLM (role: tool)
                if json_body and "messages" in json_body:
                    messages = json_body["messages"][:]
                    for call, result in zip(tool_calls, tool_results):
                        messages.append({
                            "role": "tool",
                            "tool_call_id": result["tool_call_id"],
                            "content": result["output"]
                        })
                    # Re-ask the LLM with the tool results
                    new_payload = dict(json_body)
                    new_payload["messages"] = messages
                    async with httpx.AsyncClient(timeout=6000) as client:
                        final_resp = await client.request(method, url, headers=headers, json=new_payload)
                    logger.info(f"Tool call handled, returning LLM response after tool execution.")
                    return Response(
                        content=final_resp.content,
                        status_code=final_resp.status_code,
                        media_type=final_resp.headers.get("content-type", "application/json"),
                    )
            # If no tool call, just return the original response
            logger.info(f"No tool call detected, returning original LLM response.")
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                media_type=resp.headers.get("content-type", "application/json"),
            )
        except Exception as e:
            logger.exception(f"Tool proxy Exception: {str(e)}")
            return Response(content=json.dumps({"error": str(e)}), status_code=500)
    # For all other requests, just proxy as before
    try:
        async with httpx.AsyncClient(timeout=6000) as client:
            resp = await client.request(method, url, headers=headers, content=body)
        logger.info(f"Outgoing {method} {request.url.path} status: {resp.status_code}")
        logger.info(f"Outgoing {method} {request.url.path} response headers: {dict(resp.headers)}")
        try:
            logger.info(f"Outgoing {method} {request.url.path} response body: {resp.text}")
        except Exception:
            logger.info(f"Outgoing {method} {request.url.path} response body: <binary>")
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            media_type=resp.headers.get("content-type", "application/json"),
        )
    except Exception as e:
        logger.exception(f"Logging proxy Exception: {str(e)}")
        return Response(content=json.dumps({"error": str(e)}), status_code=500)


def main():
    global DEBUG_MODE
    parser = argparse.ArgumentParser(description="Logging-only Codex Proxy for OpenAI-compatible APIs")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging to codex-proxy-logging.log")
    args = parser.parse_args()
    if args.debug:
        DEBUG_MODE = True
        logger.setLevel(logging.DEBUG)
        logger.info("Debug mode enabled.")
    uvicorn.run(app, host="0.0.0.0", port=1234)

if __name__ == "__main__":
    main()
