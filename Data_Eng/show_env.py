from pathlib import Path

content = Path('.env').read_text(encoding='utf-8')
print(repr(content))