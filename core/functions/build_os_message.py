import platform

def build_os_message() -> str:
    return f"You are running in a {platform.system()} environment. Use appropriate shell commands for this OS."
