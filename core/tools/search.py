import re
import glob
import os

def search(
    pattern,
    file_or_glob = "**/*.*",
    regex = False,
    ignore_case = True,
    root_dir = None,
    include_ignored = False,
    binary = False,
    context_lines = 0,
    max_results = None
):
    """
    Advanced search for text or regex patterns in one file or across multiple files using glob patterns.
    Returns a list of dicts with file_path, line_number, line_content, and optional context.
    Args:
        pattern: Text/regex pattern or list of patterns to search for.
        file_or_glob: File path or glob pattern (e.g., 'myfile.py' or '**/*.py').
        regex: If True, treat pattern(s) as regex.
                    with open(file_path, encoding="utf-8", errors="replace") as f:
        root_dir: Workspace root directory (defaults to current directory).
        include_ignored: If True, include files/folders normally ignored (e.g., .gitignore).
        binary: If True, search binary files (default: False).
        context_lines: Number of lines before/after match to include.
        max_results: Maximum number of results to return.
    """
    results = []
    flags = re.IGNORECASE if ignore_case else 0
    root = root_dir or os.getcwd()
    patterns = pattern if isinstance(pattern, list) else [pattern]
    # Expand glob, optionally include ignored files (simple implementation)
    if include_ignored:
        # Use os.walk for full traversal
        file_list = []
        for dirpath, _, filenames in os.walk(root):
            for fname in filenames:
                file_path = os.path.join(dirpath, fname)
                if glob.fnmatch.fnmatch(file_path, file_or_glob):
                    file_list.append(file_path)
    else:
        file_list = glob.glob(os.path.join(root, file_or_glob), recursive=True)
    for file_path in file_list:
        if not os.path.isfile(file_path):
            continue
        # Optionally skip binary files
        if not binary:
            try:
                with open(file_path, 'rb') as bf:
                    if b'\x00' in bf.read(1024):
                        continue
            except Exception:
                continue
        try:
                with open(file_path, encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    matched = False
                    for pat in patterns:
                        if regex:
                            if re.search(pat, line, flags):
                                matched = True
                                break
                        else:
                            if (pat.lower() if ignore_case else pat) in (line.lower() if ignore_case else line):
                                matched = True
                                break
                    if matched:
                        entry = {
                            "file": file_path,
                            "line": i,
                            "content": line.rstrip()
                        }
                        # Add context lines
                        if context_lines > 0:
                            start = max(0, i - 1 - context_lines)
                            end = min(len(lines), i + context_lines)
                            entry["context_before"] = [l.rstrip() for l in lines[start:i-1]]
                            entry["context_after"] = [l.rstrip() for l in lines[i:end]]
                        results.append(entry)
                        if max_results and len(results) >= max_results:
                            return results
        except Exception as e:
            results.append({"file": file_path, "line": -1, "content": f"Error: {e}"})
            if max_results and len(results) >= max_results:
                return results
        return results
# for file, line_num, content in matches:
#     print(f"{file}:{line_num}: {content}")
