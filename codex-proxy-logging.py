# Logging-only proxy for Codex/OpenAI APIs
# This version logs all incoming requests and outgoing responses, but does not translate or modify any API payloads.

import argparse
import logging
from fastapi import FastAPI, Request, Response
import httpx
import uvicorn
import os
import json

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
target_openai_url = os.environ.get("VLLM_API_URL", "http://localhost:11434")

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
        async with httpx.AsyncClient() as client:
            resp = await client.request(method, url, headers=headers, content=body)
        # Log outgoing response
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
