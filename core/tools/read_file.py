import os

def read_file(file_path, encoding="utf-8", errors="replace", max_lines=None, as_list=False):
    """
    Reads a file and returns its contents.
    Args:
        file_path: Path to the file to read.
        encoding: File encoding (default: utf-8).
        errors: Error handling for decoding (default: replace).
        max_lines: If set, only read up to this many lines.
        as_list: If True, return a list of lines; else, return a single string.
    Returns:
        File contents as a string or list of lines.
        If file does not exist, returns None.
    """
    if not os.path.isfile(file_path):
        return None
    try:
        with open(file_path, encoding=encoding, errors=errors) as f:
            if max_lines is not None:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip("\n"))
                return lines if as_list else "\n".join(lines)
            else:
                if as_list:
                    return [line.rstrip("\n") for line in f]
                else:
                    return f.read()
    except Exception as e:
        return f"Error reading file: {e}"
