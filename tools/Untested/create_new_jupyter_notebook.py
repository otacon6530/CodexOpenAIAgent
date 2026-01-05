import json
import os

metadata = {
    'name': 'create_new_jupyter_notebook',
    'description': 'Generate a new .ipynb notebook scaffold.'
}


def run(args: str) -> str:
    path = args.strip() or 'notebook.ipynb'
    notebook = {
        'cells': [],
        'metadata': {},
        'nbformat': 4,
        'nbformat_minor': 5,
    }
    try:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as handle:
            json.dump(notebook, handle, indent=2)
        return f'Created notebook {path}.'
    except Exception as exc:
        return f'create_new_jupyter_notebook error: {exc}'
