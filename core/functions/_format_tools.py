
def _format_tools(tools):
    return "\n".join([f"- {name}: {meta['description']}" for name, meta in tools.items()])

