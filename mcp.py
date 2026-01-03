#!/usr/bin/env python3
import sys
import json
import uuid

def send(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()

# Send "initialize" response
send({
    "jsonrpc": "2.0",
    "id": 0,
    "result": {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {
                "hello_tool": {
                    "description": "Returns a greeting",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"}
                        },
                        "required": ["name"]
                    }
                }
            },
            "resources": {
                "/greeting": {
                    "description": "A static greeting resource"
                }
            }
        }
    }
})

# Main loop
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)

    if req.get("method") == "tools/hello_tool":
        name = req["params"]["arguments"]["name"]
        send({
            "jsonrpc": "2.0",
            "id": req["id"],
            "result": {
                "content": f"Hello, {name}!"
            }
        })

    elif req.get("method") == "resources/read":
        if req["params"]["uri"] == "/greeting":
            send({
                "jsonrpc": "2.0",
                "id": req["id"],
                "result": {
                    "content": "Hello from MCP!"
                }
            })