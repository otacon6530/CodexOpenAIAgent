# Codex Chat Visual Studio Extension

This folder hosts a VSIX extension that surfaces the Codex agent as a dockable chat tool window inside Visual Studio. It reuses the Python conversation logic from the `core/` package by launching the reusable bridge in `core/chat_process.py` and piping requests and responses through a JSON protocol.

## Prerequisites
- Visual Studio 2022 (17.6 or later) with the Visual Studio extension development workload.
- Python 3.10+ available on your PATH (or provide a specific interpreter path in the tool window).
- The repository cloned locally. Set `CODEX_AGENT_ROOT` to the repository root if you want the extension to auto-populate the workspace path field.
- The Python dependencies listed in `requirements.txt` installed in your environment.

## Project layout
```
VSPlugin/
  CodexChatExtension.sln                # Solution entry point
  CodexChatExtension/                   # VSIX project
    CodexChatExtension.csproj
    source.extension.vsixmanifest
    CodexChatExtensionPackage.cs        # AsyncPackage bootstrap
    Commands/OpenChatWindowCommand.cs   # Command that opens the tool window
    ToolWindows/CodexChatWindow*.xaml   # WPF UI and backing logic
    Services/PythonChatClient.cs        # Manages the Python bridge process
    Services/JoinableTaskExtensions.cs  # Helper for background tasks
    Models/                             # JSON response models
```

## Building the extension
1. Open `VSPlugin/CodexChatExtension.sln` in Visual Studio 2022.
2. Restore NuGet packages if prompted.
3. Build the solution. The VSIX payload will be generated under `bin/Debug` (or `bin/Release`).
4. Press `F5` to launch an experimental Visual Studio instance with the extension installed.

## Using the chat window
1. In the experimental instance, open **Extensions > Codex Chat...** to display the tool window (the command lives under the Tools menu group).
2. Provide the workspace path pointing to this repository root (auto-filled when `CODEX_AGENT_ROOT` is set).
3. Optionally adjust the Python executable path (defaults to `python`).
4. Click **Connect**. The extension spawns `python -u -m core.chat_process` and streams responses from the agent.
5. Use the message box at the bottom to chat. Buttons let you toggle debug timing, list tools, or reset the session. All debug timing emitted by the Python side appears in the debug list on the right.

## JSON bridge protocol
The bridge launched at `core/chat_process.py` exposes a simple newline-delimited JSON protocol:
- `{"type": "message", "content": "..."}` sends a user prompt.
- `{"type": "toggle_debug"}` flips the debug metrics flag.
- Responses arrive as JSON objects with `type` (`ready`, `assistant`, `notification`, or `error`), optional `content`, `extras`, and `debug` arrays.

## Notes
- The extension runs the Python process in the supplied workspace directory so it can import the `core` package and discover local tools.
- MCP discovery runs automatically; failures are reported back to the debug pane but do not crash the chat.
- Shut down the tool window (or disconnect) to terminate the Python bridge cleanly.
