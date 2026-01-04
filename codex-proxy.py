# Logging-only proxy for Codex/OpenAI APIs
# This version logs all incoming requests and outgoing responses, but does not translate or modify any API payloads.


import argparse
import logging
from fastapi import FastAPI, Request, Response
import httpx
import uvicorn
import os
import json
import asyncio
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

# --- Codex Agent Protocol SSE tool call handler ---
import re
def parse_sse_lines(text):
    """Yields (event, data) tuples from SSE text."""
    event, data = None, []
    for line in text.splitlines():
        if line.startswith('event:'):
            event = line[len('event:'):].strip()
        elif line.startswith('data:'):
            data.append(line[len('data:'):].strip())
        elif line.strip() == '':
            if event and data:
                yield event, '\n'.join(data)
            event, data = None, []
    if event and data:
        yield event, '\n'.join(data)

def detect_and_handle_codex_tool_calls(body):
    """
    Buffers function_call events by call_id, collects arguments from function_call_arguments.done,
    and only executes the tool and emits the result after arguments are complete.
    Returns modified SSE stream (as bytes).
    """
    output_lines = []
    # Buffer for function_call events and arguments by call_id
    call_buffer = {}
    # Map item_id to call_id (for argument events)
    itemid_to_callid = {}
    for event, data in parse_sse_lines(body.decode(errors='replace')):
        output_lines.append(f"event: {event}\ndata: {data}\n")
        # Buffer function_call event
        if event == "response.output_item.added":
            try:
                item = json.loads(data).get("item", {})
                if item.get("type") == "function_call":
                    call_id = item.get("call_id")
                    item_id = item.get("id")
                    if call_id:
                        call_buffer[call_id] = {"item": item, "arguments": None, "item_id": item_id}
                        if item_id:
                            itemid_to_callid[item_id] = call_id
            except Exception:
                pass
        # Buffer arguments as they arrive
        elif event == "response.function_call_arguments.done":
            try:
                d = json.loads(data)
                item_id = d.get("item_id")
                arguments = d.get("arguments")
                if item_id and arguments:
                    call_id = itemid_to_callid.get(item_id)
                    if call_id and call_id in call_buffer:
                        call_buffer[call_id]["arguments"] = arguments
                        # Now execute the tool
                        args = json.loads(arguments)
                        # Hard-code tool name to 'exec_command' for all tool calls
                        tool_name = "exec_command"
                        tool_result = run_tool(tool_name, args)
                        item = call_buffer[call_id]["item"]
                        result_event = {
                            "arguments": arguments,
                            "call_id": call_id,
                            "id": item.get("id"),
                            "name": tool_name,
                            "status": "completed",
                            "type": "function_call_result",
                            "result": tool_result,
                        }
                        output_lines.append(f"event: response.function_call_result\ndata: {json.dumps(result_event)}\n")
            except Exception:
                pass
    return ''.join(output_lines).encode()

# Base URL for your OpenAI-compatible server
# Example: export VLLM_API_URL="http://localhost:11434"
target_openai_url = os.environ.get("VLLM_API_URL", "http://apple.stephensdev.com:11434")


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def logging_proxy(request: Request, path: str):
    method = request.method
    url = f"{target_openai_url}/{path}"
    headers = dict(request.headers)
    headers.pop("host", None)
    body = await request.body()

    # Log incoming request
    logger.info(f"Incoming {method} {request.url.path} headers: {json.dumps(headers)}")
    if body:
        try:
            logger.info(f"Incoming {method} {request.url.path} body: {body.decode(errors='replace')}")
        except Exception:
            logger.info(f"Incoming {method} {request.url.path} body: <binary>")

    try:
        async with httpx.AsyncClient(timeout=6000) as client:
            resp = await client.request(method, url, headers=headers, content=body)
        # Log outgoing response
        logger.info(f"Outgoing {method} {request.url.path} status: {resp.status_code}")
        logger.info(f"Outgoing {method} {request.url.path} response headers: {dict(resp.headers)}")
        try:
            logger.info(f"Outgoing {method} {request.url.path} response body: {resp.text}")
        except Exception:
            logger.info(f"Outgoing {method} {request.url.path} response body: <binary>")

        # If this is an SSE response, handle Codex tool calls and strip 'reasoning'
        content_type = resp.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            # First, handle Codex tool calls
            sse_content = detect_and_handle_codex_tool_calls(resp.content)
            # Now patch streaming SSE responses: remove 'reasoning' from each chunk
            try:
                lines = sse_content.decode(errors='replace').splitlines()
                patched_lines = []
                for line in lines:
                    if line.startswith("data: "):
                        try:
                            payload = json.loads(line[6:])
                            # Remove 'reasoning' from each chunk
                            choices = payload.get("choices", [])
                            for choice in choices:
                                delta = choice.get("delta", {})
                                if "reasoning" in delta:
                                    del delta["reasoning"]
                            patched_line = "data: " + json.dumps(payload)
                            patched_lines.append(patched_line)
                        except Exception:
                            patched_lines.append(line)
                    else:
                        patched_lines.append(line)
                patched_content = "\n".join(patched_lines).encode()
            except Exception as patch_err:
                logger.warning(f"Failed to patch SSE response: {patch_err}")
                patched_content = sse_content
            return Response(
                content=patched_content,
                status_code=resp.status_code,
                media_type=content_type,
            )
        else:
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
