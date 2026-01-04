import os
import json
import glob
import re
import subprocess
from typing import Callable, List, Dict


def _make_unsupported(name: str) -> Callable[[str], str]:
    def _runner(_args: str, tool: str = name) -> str:
        return f"Tool '{tool}' is not supported in this CLI environment."
    return _runner


def _create_directory(args: str) -> str:
    path = args.strip()
    if not path:
        return "create_directory error: no path provided."
    try:
        os.makedirs(path, exist_ok=True)
        return f"Created directory {path}."
    except Exception as exc:  # pragma: no cover - simple wrapper
        return f"create_directory error: {exc}"


def _create_file(args: str) -> str:
    if not args.strip():
        return "create_file error: no arguments provided."
    if '|' in args:
        path, content = args.split('|', 1)
    else:
        path, content = args, ''
    path = path.strip()
    try:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(content)
        return f"Created file {path}."
    except Exception as exc:
        return f"create_file error: {exc}"


def _create_notebook(args: str) -> str:
    path = args.strip() or 'notebook.ipynb'
    notebook = {
        "cells": [],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    try:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as handle:
            json.dump(notebook, handle, indent=2)
        return f"Created notebook {path}."
    except Exception as exc:
        return f"create_new_jupyter_notebook error: {exc}"


def _fetch_webpage(args: str) -> str:
    if not args.strip():
        return "fetch_webpage error: no URL provided."
    if '|' in args:
        url, query = args.split('|', 1)
        query = query.strip()
    else:
        url, query = args, ''
    url = url.strip()
    try:
        import requests  # type: ignore
    except ImportError:
        return "fetch_webpage error: requests library not installed."
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        text = response.text
        if query:
            match = re.search(query, text, re.IGNORECASE)
            if match:
                start = max(match.start() - 120, 0)
                end = min(match.end() + 120, len(text))
                snippet = text[start:end]
                return f"Found query snippet:\n{snippet}"
            return "Query not found in page."
        return text[:2000] + ('\n...[truncated]...' if len(text) > 2000 else '')
    except Exception as exc:
        return f"fetch_webpage error: {exc}"


def _file_search(args: str) -> str:
    pattern = args.strip()
    if not pattern:
        return "file_search error: no pattern provided."
    matches = glob.glob(pattern, recursive=True)
    if not matches:
        return "No files matched the pattern."
    matches.sort()
    return '\n'.join(matches[:200])


def _grep_search(args: str) -> str:
    if '|' not in args:
        return "grep_search usage: pattern|filename."
    pattern, filename = args.split('|', 1)
    pattern = pattern.strip()
    filename = filename.strip()
    if not pattern or not filename:
        return "grep_search error: pattern and filename required."
    if not os.path.exists(filename):
        return f"grep_search error: {filename} not found."
    try:
        with open(filename, 'r', encoding='utf-8') as handle:
            content = handle.read()
        matches = re.findall(pattern, content, flags=re.MULTILINE)
        if not matches:
            return "No matches found."
        sample = matches[:5]
        return f"Found {len(matches)} matches: {sample}"
    except Exception as exc:
        return f"grep_search error: {exc}"


def _get_changed_files(_args: str) -> str:
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, timeout=10)
        output = result.stdout.strip()
        return output or 'No changes.'
    except Exception as exc:
        return f"get_changed_files error: {exc}"


def _list_dir(args: str) -> str:
    path = args.strip() or '.'
    if not os.path.exists(path):
        return f"list_dir error: {path} not found."
    try:
        entries = sorted(os.listdir(path))
        return '\n'.join(entries)
    except Exception as exc:
        return f"list_dir error: {exc}"


def _read_file(args: str) -> str:
    if not args.strip():
        return "read_file error: no arguments provided."
    parts = [part.strip() for part in args.split('|')]
    path = parts[0]
    start = int(parts[1]) if len(parts) > 1 and parts[1] else None
    end = int(parts[2]) if len(parts) > 2 and parts[2] else None
    if not os.path.exists(path):
        return f"read_file error: {path} not found."
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            lines = handle.readlines()
        start_idx = start - 1 if start else 0
        end_idx = end if end else len(lines)
        selected = ''.join(lines[start_idx:end_idx])
        return selected if selected else '(No content in specified range)'
    except Exception as exc:
        return f"read_file error: {exc}"


def _run_in_terminal(args: str) -> str:
    command = args.strip()
    if not command:
        return "run_in_terminal error: no command provided."
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout.strip()
        error = result.stderr.strip()
        if result.returncode != 0:
            return f"Command failed (code {result.returncode}): {error or output}"
        return output or '(No output)'
    except Exception as exc:
        return f"run_in_terminal error: {exc}"


_supported_tools: List[Dict[str, object]] = [
    {
        'name': 'create_directory',
        'description': 'Recursively create folders (mkdir -p).',
        'run': _create_directory,
    },
    {
        'name': 'create_file',
        'description': 'Create a new file with given content.',
        'run': _create_file,
    },
    {
        'name': 'create_new_jupyter_notebook',
        'description': 'Generate a new .ipynb notebook scaffold.',
        'run': _create_notebook,
    },
    {
        'name': 'fetch_webpage',
        'description': 'Download and parse webpage content for summarization.',
        'run': _fetch_webpage,
    },
    {
        'name': 'file_search',
        'description': 'Glob search for filenames within workspace.',
        'run': _file_search,
    },
    {
        'name': 'grep_search',
        'description': 'Regex or plain-text search across files.',
        'run': _grep_search,
    },
    {
        'name': 'get_changed_files',
        'description': 'List git changes (staged/unstaged/conflicts).',
        'run': _get_changed_files,
    },
    {
        'name': 'list_dir',
        'description': 'Directory listing (files and subfolders).',
        'run': _list_dir,
    },
    {
        'name': 'read_file',
        'description': 'Read file contents by line range.',
        'run': _read_file,
    },
    {
        'name': 'run_in_terminal',
        'description': 'Execute PowerShell commands in persistent terminal.',
        'run': _run_in_terminal,
    },
]


_unsupported_definitions = [
    ("apply_patch", "Patch existing files using V4A diff format."),
    ("create_new_workspace", "Scaffold a full project/workspace from scratch."),
    ("edit_notebook_file", "Edit cells inside an existing Jupyter notebook."),
    ("get_errors", "Retrieve diagnostics/lint errors from analyzer."),
    ("copilot_getNotebookSummary", "List notebook cells, metadata, execution order."),
    ("get_project_setup_info", "Guided setup steps for full project scaffolds."),
    ("get_vscode_api", "Query VS Code extension API documentation."),
    ("github_repo", "Search external GitHub repositories for code snippets."),
    ("install_extension", "Install a VS Code extension (new workspace setup)."),
    ("list_code_usages", "Find references/definitions/usages of a symbol."),
    ("open_simple_browser", "Open URL in VS Code Simple Browser."),
    ("run_notebook_cell", "Execute a specific Jupyter notebook cell."),
    ("run_vscode_command", "Invoke a VS Code command (new workspace setup)."),
    ("semantic_search", "Natural-language search across workspace files."),
    ("get_search_view_results", "Return the current VS Code Search view results."),
    ("test_failure", "Report previously captured test failures."),
    ("vscode_searchExtensions_internal", "Search VS Code Marketplace for extensions."),
    ("configure_python_environment", "Select/configure Python interpreter for workspace."),
    ("get_python_environment_details", "List packages/version for configured Python env."),
    ("get_python_executable_details", "Retrieve executable invocation details for Python env."),
    ("install_python_packages", "Install packages into active Python environment."),
    ("manage_todo_list", "Track multi-step plans via shared todo list."),
    ("mcp_pylance_mcp_s_pylanceDocuments", "Query Pylance documentation."),
    ("mcp_pylance_mcp_s_pylanceFileSyntaxErrors", "Check Python file for syntax errors."),
    ("mcp_pylance_mcp_s_pylanceImports", "Analyze top-level imports across workspace."),
    ("mcp_pylance_mcp_s_pylanceInstalledTopLevelModules", "List importable modules from environment."),
    ("mcp_pylance_mcp_s_pylanceInvokeRefactoring", "Apply Pylance refactorings (unused imports, etc.)."),
    ("mcp_pylance_mcp_s_pylancePythonEnvironments", "Enumerate available Python environments."),
    ("mcp_pylance_mcp_s_pylanceRunCodeSnippet", "Execute Python snippet in configured environment."),
    ("mcp_pylance_mcp_s_pylanceSettings", "Fetch python.analysis settings state."),
    ("mcp_pylance_mcp_s_pylanceSyntaxErrors", "Validate Python snippet for syntax errors."),
    ("mcp_pylance_mcp_s_pylanceUpdatePythonEnvironment", "Switch active Python environment."),
    ("mcp_pylance_mcp_s_pylanceWorkspaceRoots", "Return workspace root paths."),
    ("mcp_pylance_mcp_s_pylanceWorkspaceUserFiles", "List user Python files considered by Pylance."),
    ("get_terminal_output", "Fetch output from a previously run terminal command."),
    ("terminal_last_command", "Return the last command executed in terminal."),
    ("terminal_selection", "Return current selection from terminal buffer."),
    ("create_and_run_task", "Define and execute VS Code tasks via tasks.json."),
    ("runSubagent", "Launch autonomous agent for multi-step research or edits."),
    ("multi_tool_use.parallel", "Execute multiple tool calls in parallel when safe."),
]


for name, description in _unsupported_definitions:
    _supported_tools.append({
        'name': name,
        'description': description,
        'run': _make_unsupported(name),
    })


TOOLS = _supported_tools
