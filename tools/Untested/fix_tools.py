import pathlib

root = pathlib.Path('tools')
for path in root.glob('*.py'):
    text = path.read_text(encoding='utf-8')
    stripped = text.rstrip()
    if stripped.endswith('}'):
        new_text = stripped[:-1].rstrip() + '\n'
        path.write_text(new_text, encoding='utf-8')
        print(f'Fixed {path}')
